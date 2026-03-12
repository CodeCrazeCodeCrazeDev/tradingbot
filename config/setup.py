from setuptools import setup, find_packages

setup(
    name="trading_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.23",
        "pandas>=1.5",
        "pyyaml>=6.0",
        "loguru>=0.7",
        "nltk>=3.8",
        "TA-Lib>=0.4.24",
        "requests>=2.31.0",
        "aiohttp>=3.8.0",
        "websockets>=11.0.0",
        "plotly>=5.18.0",
        "dash>=2.14.0",
        "dash-bootstrap-components>=1.5.0",
        "scikit-learn>=1.3.0",
        "tensorflow>=2.13.0",
        "torch>=2.0.0",
        "qiskit>=0.40.0",
        "cryptography>=41.0.0",
        "mplfinance==0.12.10b0",  # Using latest beta version
        "kaleido>=0.2.1",
        "matplotlib>=3.7.0",  # Required by mplfinance
        "seaborn>=0.12.0",  # For enhanced visualizations
    ],
    python_requires=">=3.8",
)
