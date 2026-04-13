import sys, os, pytest, importlib.util
from unittest.mock import MagicMock

sys.modules['psycopg2'] = MagicMock()

BASE = r'C:\crypto-trading-bot\services\ml-decision-engine\app'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

config = load('app.config', f'{BASE}\\config.py')
predictor = load('app.predictor', f'{BASE}\\predictor.py')
predict = predictor.predict

SAMPLE_FEATURES = {
    'ma20': 73000.0, 'ma50': 72000.0, 'ma200': 65000.0,
    'rsi': 55.0, 'returns': 0.002, 'vol_20': 0.015,
    'macd': 150.0, 'macd_signal': 120.0, 'macd_diff': 30.0,
    'bb_high': 75000.0, 'bb_low': 71000.0, 'bb_mid': 73000.0,
    'bb_width': 0.05, 'bb_pct': 0.6,
    'atr': 1200.0, 'stoch_rsi': 0.6, 'stoch_rsi_k': 0.65,
    'stoch_rsi_d': 0.62, 'volume_ratio': 1.1,
    'dist_ma200': 0.12, 'dist_ma50': 0.01,
    'hour': 14.0, 'day_of_week': 2.0,
    'close_lag_1': 72800.0, 'returns_lag_1': 0.001,
    'close_lag_2': 72600.0, 'returns_lag_2': 0.002,
    'close_lag_3': 72400.0, 'returns_lag_3': 0.003,
    'close_lag_6': 72000.0, 'returns_lag_6': 0.005,
    'close_lag_12': 71500.0, 'returns_lag_12': 0.007,
    'close_lag_24': 70000.0, 'returns_lag_24': 0.04,
}

class TestPredictor:
    def test_predict_btc_returns_valid_signal(self):
        result = predict('BTC/USDT', SAMPLE_FEATURES)
        assert result['signal'] in ['BUY', 'SELL', 'HOLD']

    def test_predict_eth_returns_valid_signal(self):
        assert predict('ETH/USDT', SAMPLE_FEATURES)['signal'] in ['BUY', 'SELL', 'HOLD']

    def test_predict_returns_confidence(self):
        result = predict('BTC/USDT', SAMPLE_FEATURES)
        assert 0.0 <= result['confidence'] <= 100.0

    def test_predict_returns_model_name(self):
        result = predict('BTC/USDT', SAMPLE_FEATURES)
        assert isinstance(result['model'], str) and len(result['model']) > 0

    def test_predict_invalid_symbol_raises(self):
        with pytest.raises(ValueError):
            predict('INVALID/USDT', SAMPLE_FEATURES)

    def test_predict_missing_features_raises(self):
        with pytest.raises(Exception):
            predict('BTC/USDT', {})

    def test_predict_btc_uses_neural_network(self):
        assert 'Neural Network' in predict('BTC/USDT', SAMPLE_FEATURES)['model']

    def test_predict_eth_uses_xgboost(self):
        assert 'XGBoost' in predict('ETH/USDT', SAMPLE_FEATURES)['model']