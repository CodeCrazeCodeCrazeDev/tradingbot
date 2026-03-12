"""
Comprehensive tests for explainability modules
"""

import pytest
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier


class TestLIMEExplainer:
    """Test LIME explainability"""
    
    def test_lime_initialization(self):
        from trading_bot.ml.explainability import LIMEExplainer
        
        X_train = np.random.randn(100, 10)
        feature_names = [f'feature_{i}' for i in range(10)]
        
        try:
            explainer = LIMEExplainer(X_train, feature_names, mode='regression')
            assert explainer.feature_names == feature_names
        except ImportError:
            pytest.skip("LIME not installed")
    
    def test_lime_explain_regression(self):
        try:
            X_train = np.random.randn(100, 10)
            y_train = np.random.randn(100)
            
            model = RandomForestRegressor(n_estimators=5, random_state=42)
            model.fit(X_train, y_train)
            
            feature_names = [f'feature_{i}' for i in range(10)]
            explainer = LIMEExplainer(X_train, feature_names, mode='regression')
            
            test_instance = np.random.randn(10)
            explanation = explainer.explain_prediction(model, test_instance, num_features=5)
            
            assert 'feature_importance' in explanation
            assert 'local_prediction' in explanation
            assert len(explanation['feature_importance']) <= 5
        except ImportError:
            pytest.skip("LIME not installed")
    
    def test_lime_explain_classification(self):
        try:
            X_train = np.random.randn(100, 10)
            y_train = np.random.randint(0, 2, 100)
            
            model = RandomForestClassifier(n_estimators=5, random_state=42)
            model.fit(X_train, y_train)
            
            feature_names = [f'feature_{i}' for i in range(10)]
            explainer = LIMEExplainer(
                X_train, 
                feature_names, 
                class_names=['class_0', 'class_1'],
                mode='classification'
            )
            
            test_instance = np.random.randn(10)
            explanation = explainer.explain_prediction(model, test_instance)
            
            assert 'feature_importance' in explanation
        except ImportError:
            pytest.skip("LIME not installed")
    
    def test_lime_top_features(self):
        try:
            X_train = np.random.randn(100, 10)
            y_train = np.random.randn(100)
            
            model = RandomForestRegressor(n_estimators=5, random_state=42)
            model.fit(X_train, y_train)
            
            feature_names = [f'feature_{i}' for i in range(10)]
            explainer = LIMEExplainer(X_train, feature_names)
            
            test_instance = np.random.randn(10)
            explanation = explainer.explain_prediction(model, test_instance)
            
            top_features = explainer.get_top_features(explanation, n=3)
            assert len(top_features) <= 3
        except ImportError:
            pytest.skip("LIME not installed")


class TestTradingLIMEExplainer:
    """Test trading-specific LIME explainer"""
    
    def test_trading_lime_initialization(self):
        from trading_bot.ml.explainability import TradingLIMEExplainer
        
        try:
            X_train = np.random.randn(100, 10)
            feature_names = [f'feature_{i}' for i in range(10)]
            
            explainer = TradingLIMEExplainer(X_train, feature_names)
            assert explainer.feature_names == feature_names
        except ImportError:
            pytest.skip("LIME not installed")
    
    def test_explain_trade_signal(self):
        import pandas as pd
        
        try:
            X_train = np.random.randn(100, 5)
            y_train = np.random.randn(100)
            
            model = RandomForestRegressor(n_estimators=5, random_state=42)
            model.fit(X_train, y_train)
            
            feature_columns = ['rsi', 'macd', 'atr', 'volume', 'price']
            explainer = TradingLIMEExplainer(X_train, feature_columns)
            
            market_data = pd.DataFrame(
                np.random.randn(50, 5),
                columns=feature_columns
            )
            
            explanation = explainer.explain_trade_signal(model, market_data, feature_columns)
            
            assert 'bullish_factors' in explanation
            assert 'bearish_factors' in explanation
            assert 'net_sentiment' in explanation
        except ImportError:
            pytest.skip("LIME not installed")
    
    def test_generate_explanation_text(self):
        try:
            explanation = {
                'local_prediction': 0.75,
                'net_sentiment': 0.15,
                'bullish_factors': [('rsi', 0.25), ('macd', 0.15)],
                'bearish_factors': [('atr', -0.10)]
            }
            
            X_train = np.random.randn(100, 3)
            explainer = TradingLIMEExplainer(X_train, ['rsi', 'macd', 'atr'])
            
            text = explainer.generate_explanation_text(explanation)
            
            assert 'Prediction' in text
            assert 'Bullish' in text
            assert 'Bearish' in text
        except ImportError:
            pytest.skip("LIME not installed")


class TestSHAPExplainer:
    """Test SHAP explainability (if available)"""
    
    def test_shap_available(self):

            from trading_bot.ml.explainability import SHAPExplainer
import numpy
import pandas
assert True




if __name__ == "__main__":
    pytest.main([__file__, "-v"])
