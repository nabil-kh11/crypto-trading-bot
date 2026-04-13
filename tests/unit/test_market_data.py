import sys, os, importlib.util
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

sys.modules['ccxt'] = MagicMock()

BASE = r'C:\crypto-trading-bot\services\market-data-collector\app'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

sys.modules['app.config'] = MagicMock(TIMEFRAME='1h', FETCH_LIMIT=100)
collector = load('app.collector', f'{BASE}\\collector.py')
_add_indicators = collector._add_indicators

def get_sample_df(rows=300):
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=rows, freq='1h')
    close = 70000 + np.cumsum(np.random.randn(rows) * 100)
    return pd.DataFrame({
        'timestamp': dates,
        'open':   close + np.random.randn(rows) * 50,
        'high':   close + abs(np.random.randn(rows) * 150),
        'low':    close - abs(np.random.randn(rows) * 150),
        'close':  close,
        'volume': abs(np.random.randn(rows) * 1000 + 5000),
    })

class TestFeatureEngineering:
    def test_add_indicators_returns_dataframe(self):
        assert isinstance(_add_indicators(get_sample_df()), pd.DataFrame)

    def test_add_indicators_has_rsi(self):
        assert 'rsi' in _add_indicators(get_sample_df()).columns

    def test_add_indicators_has_ma20(self):
        assert 'ma20' in _add_indicators(get_sample_df()).columns

    def test_add_indicators_has_ma50(self):
        assert 'ma50' in _add_indicators(get_sample_df()).columns

    def test_add_indicators_has_ma200(self):
        assert 'ma200' in _add_indicators(get_sample_df()).columns

    def test_add_indicators_has_macd(self):
        result = _add_indicators(get_sample_df())
        assert 'macd' in result.columns and 'macd_signal' in result.columns

    def test_add_indicators_has_bollinger(self):
        result = _add_indicators(get_sample_df())
        for col in ['bb_high','bb_low','bb_mid','bb_width','bb_pct']:
            assert col in result.columns

    def test_add_indicators_has_atr(self):
        assert 'atr' in _add_indicators(get_sample_df()).columns

    def test_add_indicators_rsi_range(self):
        result = _add_indicators(get_sample_df()).dropna()
        assert result['rsi'].between(0, 100).all()

    def test_add_indicators_has_35_features(self):
        COLS = [
            'ma20','ma50','ma200','rsi','returns','vol_20',
            'macd','macd_signal','macd_diff',
            'bb_high','bb_low','bb_mid','bb_width','bb_pct',
            'atr','stoch_rsi','stoch_rsi_k','stoch_rsi_d',
            'volume_ratio','dist_ma200','dist_ma50',
            'hour','day_of_week',
            'close_lag_1','returns_lag_1','close_lag_2','returns_lag_2',
            'close_lag_3','returns_lag_3','close_lag_6','returns_lag_6',
            'close_lag_12','returns_lag_12','close_lag_24','returns_lag_24'
        ]
        result = _add_indicators(get_sample_df())
        for col in COLS:
            assert col in result.columns, f"Missing: {col}"