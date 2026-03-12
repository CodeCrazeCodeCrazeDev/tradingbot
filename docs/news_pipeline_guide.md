# News Pipeline Module - Usage Guide

This guide explains how to use the Elite Trading Bot's News Pipeline module to enhance trading decisions with real-time financial news and sentiment analysis.

## Overview

The News Pipeline module provides a comprehensive system for:

1. Fetching financial news articles from multiple sources (NewsAPI, RSS feeds)
2. Processing and analyzing text content
3. Embedding articles using sentence-transformers for semantic understanding
4. Indexing embeddings in FAISS for efficient similarity search
5. Generating structured trading signals based on news sentiment and relevance

## Quick Start

To enable news-based sentiment analysis in your trading bot, use the `--sentiment-analysis` flag along with internet access:

```bash
python main.py --symbol EURUSD --timeframe H1 --bars 500 --mode paper --use-ml \
  --sentiment-analysis --internet-access --news-api-key YOUR_NEWSAPI_KEY
```

## Command-Line Arguments

The following command-line arguments control the News Pipeline:

| Argument | Description |
|----------|-------------|
| `--sentiment-analysis` | Enable market sentiment analysis |
| `--internet-access` | Enable internet connectivity (required for news fetching) |
| `--news-api-key` | Your NewsAPI API key (optional) |
| `--news-data-dir` | Directory for storing news data (default: ./data/news) |

## Integration with Trading Strategies

The News Pipeline integrates with the Elite Trading Bot's ML strategy engine to provide sentiment signals that can influence trading decisions.

### How News Signals Affect Trading

1. **Sentiment Score**: Each news article is assigned a sentiment score (-1.0 to 1.0) indicating bearish to bullish sentiment
2. **Confidence**: Indicates how reliable the sentiment assessment is (based on source credibility)
3. **Impact**: Measures the potential market impact (based on recency and sentiment strength)
4. **Relevance**: How relevant the news is to the specific asset being traded

These factors are combined to generate trading signals that can:
- Adjust position sizing
- Modify entry/exit timing
- Filter out false signals from technical indicators
- Provide early warning of potential market moves

## Using the News Pipeline in Custom Code

### Basic Usage

```python
from trading_bot.intel.news_pipeline import NewsPipeline

# Initialize the pipeline
news_pipeline = NewsPipeline(
    newsapi_key="YOUR_NEWSAPI_KEY",
    data_dir="./data/news"
)

# Refresh news for specific assets
await news_pipeline.refresh(assets=["EURUSD", "GBPUSD"])

# Generate trading signals
signals = await news_pipeline.generate_signals(["EURUSD"])

# Use signals in your strategy
for signal in signals:
    print(f"Asset: {signal.asset}")
    print(f"Sentiment: {signal.sentiment:.2f}")
    print(f"Confidence: {signal.confidence:.2f}")
    print(f"Impact: {signal.impact:.2f}")
    print(f"Source: {signal.source}")
    print(f"Title: {signal.title}")
    print(f"URL: {signal.url}")
    print(f"Published: {signal.published_at}")
    print(f"Summary: {signal.summary}")
```

### Querying for Specific News

You can also query the news database for articles related to specific topics:

```python
# Query for articles about interest rates
articles = await news_pipeline.query(
    "interest rates federal reserve hike",
    assets=["USD", "EUR"],
    top_k=5
)

for article in articles:
    print(f"Title: {article.title}")
    print(f"Source: {article.source}")
    print(f"Published: {article.published_at}")
    print(f"Sentiment: {article.sentiment_score:.2f}")
    print(f"URL: {article.url}")
    print(f"Summary: {article.summary}")
    print("---")
```

## Advanced Configuration

### Custom News Sources

The News Pipeline uses both NewsAPI and RSS feeds by default. You can customize the RSS feeds by modifying the `_fetch_from_rss` method:

```python
# Example of adding custom RSS feeds
feeds = [
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://www.reuters.com/business/finance/rssfeeds",
    "https://feeds.finance.yahoo.com/rss/2.0/headline",
    "https://www.ft.com/markets?format=rss",
    "https://your-custom-feed.com/rss"  # Add your custom feed here
]
```

### Adjusting Sentiment Analysis

The sentiment analysis uses NLTK's VADER sentiment analyzer by default. You can adjust the sentiment thresholds or implement a custom sentiment analyzer:

```python
# Example of custom sentiment analysis
def custom_sentiment_analyzer(text):
    # Your custom sentiment analysis logic here
    return sentiment_score  # -1.0 to 1.0
    
# Replace the default sentiment analyzer
news_pipeline.sentiment_analyzer = custom_sentiment_analyzer
```

### Caching and Performance

The News Pipeline includes caching to minimize API requests and improve performance:

- News articles are cached on disk in the specified `data_dir`
- FAISS index is saved for fast vector similarity search
- Automatic refresh interval prevents excessive API calls

You can adjust these settings when initializing the pipeline:

```python
news_pipeline = NewsPipeline(
    newsapi_key="YOUR_NEWSAPI_KEY",
    data_dir="./data/news",
    max_articles=2000,        # Maximum articles to keep in memory
    refresh_interval=1800     # Seconds between refreshes (30 minutes)
)
```

## Example: Creating a News-Based Trading Strategy

Here's an example of how to create a simple trading strategy that incorporates news sentiment:

```python
from trading_bot.strategy import StrategyEngine
from trading_bot.intel.news_pipeline import NewsPipeline

class NewsSentimentStrategy(StrategyEngine):
    def __init__(self, mt5i, symbol, **kwargs):
        super().__init__(mt5i, symbol, **kwargs)
        self.news_pipeline = NewsPipeline(
            newsapi_key=kwargs.get("news_api_key")
        )
        
    async def analyse(self, df, **kwargs):
        # Get technical signals
        signals = super().analyse(df)
        
        # Get news signals
        news_signals = await self.news_pipeline.generate_signals([self.symbol])
        
        # Filter signals based on news sentiment
        if news_signals:
            top_signal = news_signals[0]
            
            # If strong negative sentiment, filter out buy signals
            if top_signal.sentiment < -0.5 and top_signal.impact > 0.7:
                signals = [s for s in signals if s.direction != "buy"]
                
            # If strong positive sentiment, filter out sell signals
            elif top_signal.sentiment > 0.5 and top_signal.impact > 0.7:
                signals = [s for s in signals if s.direction != "sell"]
                
            # Add news sentiment to signal metadata
            for signal in signals:
                if not hasattr(signal, "metadata"):
                    signal.metadata = {}
                signal.metadata["news_sentiment"] = top_signal.sentiment
                signal.metadata["news_impact"] = top_signal.impact
                signal.metadata["news_title"] = top_signal.title
        
        return signals
```

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure your NewsAPI key is valid and has not exceeded its quota
   - Set the key as an environment variable: `export NEWSAPI_KEY=your_key_here`

2. **No News Found**
   - Check that your asset symbols are commonly used in news articles
   - Try broader terms (e.g., "USD" instead of "EURUSD")
   - Ensure internet connectivity is working

3. **Performance Issues**
   - Reduce `max_articles` if memory usage is high
   - Increase `refresh_interval` to reduce API calls
   - Use a smaller sentence transformer model

### Logging

The News Pipeline uses the standard logging module. To see detailed logs:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("trading_bot.intel.news_pipeline").setLevel(logging.DEBUG)
```

## Dependencies

The News Pipeline requires the following dependencies:

- sentence-transformers
- faiss-cpu
- nltk
- feedparser
- beautifulsoup4
- requests
- numpy
- pandas

These are automatically installed when you install the Elite Trading Bot with the provided requirements.txt file.

## Further Reading

- [FAISS Documentation](https://github.com/facebookresearch/faiss/wiki)
- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [NewsAPI Documentation](https://newsapi.org/docs)
- [NLTK Sentiment Analysis](https://www.nltk.org/howto/sentiment.html)
