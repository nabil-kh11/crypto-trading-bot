import sys, os, importlib.util
from unittest.mock import MagicMock

for mod in ['psycopg2', 'grpc', 'app', 'app.database', 'app.binance_executor',
            'app.ml_engine_pb2', 'app.ml_engine_pb2_grpc',
            'app.market_data_pb2', 'app.market_data_pb2_grpc',
            'app.config']:
    sys.modules[mod] = MagicMock()

BASE = r'C:\crypto-trading-bot\services\order-executor\app'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

load('app.config', f'{BASE}\\config.py')
executor = load('app.executor', f'{BASE}\\executor.py')

calculate_buy_size  = executor.calculate_buy_size
check_stop_loss     = executor.check_stop_loss
check_trend_filter  = executor.check_trend_filter
check_rsi_filter    = executor.check_rsi_filter
calculate_sell_size = executor.calculate_sell_size

class TestExecutorStrategy:
    def test_calculate_buy_size_low_confidence(self):
        assert calculate_buy_size(10000.0, 49.0) == 0

    def test_calculate_buy_size_minimum_confidence(self):
        assert calculate_buy_size(10000.0, 50.0) > 0

    def test_calculate_buy_size_high_confidence(self):
        assert calculate_buy_size(10000.0, 95.0) > calculate_buy_size(10000.0, 55.0)

    def test_calculate_buy_size_max_20_percent(self):
        assert calculate_buy_size(10000.0, 100.0) <= 2000.0

    def test_check_stop_loss_triggered(self):
        assert check_stop_loss(avg_buy_price=100.0, current_price=94.0) is True

    def test_check_stop_loss_not_triggered(self):
        assert check_stop_loss(avg_buy_price=100.0, current_price=97.0) is False

    def test_check_stop_loss_no_position(self):
        assert check_stop_loss(avg_buy_price=0.0, current_price=50000.0) is False

    def test_check_trend_filter_buy_downtrend(self):
        assert check_trend_filter({'ma20': 70000.0, 'ma50': 72000.0}, 'BUY') is False

    def test_check_trend_filter_buy_uptrend(self):
        assert check_trend_filter({'ma20': 74000.0, 'ma50': 72000.0}, 'BUY') is True

    def test_check_trend_filter_sell_uptrend(self):
        assert check_trend_filter({'ma20': 74000.0, 'ma50': 72000.0}, 'SELL') is False

    def test_check_rsi_filter_overbought(self):
        assert check_rsi_filter({'rsi': 75.0}, 'BUY') is False

    def test_check_rsi_filter_oversold(self):
        assert check_rsi_filter({'rsi': 25.0}, 'SELL') is False

    def test_check_rsi_filter_normal(self):
        assert check_rsi_filter({'rsi': 55.0}, 'BUY') is True

    def test_calculate_sell_size_profitable(self):
        assert calculate_sell_size(1.0, 80.0, 60000.0, 75000.0) > 0.5

    def test_calculate_sell_size_no_balance(self):
        assert calculate_sell_size(0.0, 80.0, 60000.0, 75000.0) == 0