import importlib
import sys

def hot_reload(module_name):
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
        print(f'Reloaded {module_name}')
    else:
        __import__(module_name)
        print(f'Imported {module_name}')

# Example usage:
if __name__ == '__main__':
    hot_reload('trading_bot.main')
