import sys

def test_imports():
    try:
        import pandas, numpy, MetaTrader5
        return True
    except Exception as e:
        print(f"Import test failed: {e}")
        return False

def test_config():
    try:
        import yaml
        with open('config/config.yaml') as f:
            cfg = yaml.safe_load(f)
        assert 'mt5' in cfg
        return True
    except Exception as e:
        print(f"Config test failed: {e}")
        return False

def test_api():
    try:
        import MetaTrader5 as mt5
        mt5.initialize()
        assert mt5.version() is not None
        mt5.shutdown()
        return True
    except Exception as e:
        print(f"API test failed: {e}")
        return False

def run_smoke_tests():
    results = [test_imports(), test_config(), test_api()]
    if all(results):
        print("All smoke tests passed.")
        return True
    else:
        print("One or more smoke tests failed.")
        return False

if __name__ == '__main__':
    sys.exit(0 if run_smoke_tests() else 1)
