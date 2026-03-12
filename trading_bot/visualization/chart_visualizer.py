import logging
logger = logging.getLogger(__name__)
from pathlib import Path
"""
Chart visualization module for the trading bot.

This module provides tools for visualizing price charts with signals,
support/resistance levels, and other technical indicators.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.collections import LineCollection
import mplfinance as mpf
from loguru import logger
from typing import Dict
import pathlib
import numpy
from typing import List
import pandas
from typing import Set


class ChartVisualizer:
    """
    Visualizes price charts with trading signals and technical indicators.
    
    This class provides methods to create interactive and static visualizations
    of price data, including candlestick charts, technical indicators, and
    trading signals.
    """
    
    def __init__(self, theme='dark'):
        """
        Initialize the chart visualizer.
        
        Args:
            theme: Visual theme ('dark', 'light', 'default')
        """
        self.theme = theme
        self._setup_style()
    
    def _setup_style(self):
        """Configure the matplotlib style based on the selected theme."""
        if self.theme == 'dark':
            plt.style.use('dark_background')
            self.colors = {
                'bg': '#121212',
                'text': '#e0e0e0',
                'grid': '#333333',
                'up': '#26a69a',
                'down': '#ef5350',
                'signal_buy': '#00e676',
                'signal_sell': '#ff1744',
                'support': '#42a5f5',
                'resistance': '#ff7043',
                'volume': '#546e7a',
                'prediction': '#ffeb3b',
                'confidence': '#ce93d8'
            }
        elif self.theme == 'light':
            plt.style.use('default')
            self.colors = {
                'bg': '#ffffff',
                'text': '#212121',
                'grid': '#e0e0e0',
                'up': '#26a69a',
                'down': '#ef5350',
                'signal_buy': '#00c853',
                'signal_sell': '#d50000',
                'support': '#1e88e5',
                'resistance': '#f4511e',
                'volume': '#78909c',
                'prediction': '#fdd835',
                'confidence': '#ab47bc'
            }
        else:
            plt.style.use('default')
            self.colors = {
                'bg': '#ffffff',
                'text': '#212121',
                'grid': '#e0e0e0',
                'up': '#26a69a',
                'down': '#ef5350',
                'signal_buy': '#00c853',
                'signal_sell': '#d50000',
                'support': '#1e88e5',
                'resistance': '#f4511e',
                'volume': '#78909c',
                'prediction': '#fdd835',
                'confidence': '#ab47bc'
            }
    
    def plot_candlestick(self, df, signals=None, predictions=None, support_resistance=None, 
                         indicators=None, title=None, save_path=None, show=True, figsize=(14, 10)):
        """
        Plot a candlestick chart with optional signals, predictions, and indicators.
        
        Args:
            df: DataFrame with OHLCV data
            signals: List of signal objects
            predictions: DataFrame with price predictions
            support_resistance: Dict with support and resistance levels
            indicators: Dict with technical indicators to plot
            title: Chart title
            save_path: Path to save the chart image
            show: Whether to display the chart
            figsize: Figure size tuple
            
        Returns:
            matplotlib figure object
        """
        # Ensure df has the right format for mplfinance
        df = df.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'time' in df.columns:
                df.set_index('time', inplace=True)
            else:
                df.index = pd.to_datetime(df.index)
        
        # Prepare the style
        mc = mpf.make_marketcolors(
            up=self.colors['up'],
            down=self.colors['down'],
            edge='inherit',
            wick='inherit',
            volume=self.colors['volume']
        )
        
        s = mpf.make_mpf_style(
            marketcolors=mc,
            gridstyle='-',
            gridcolor=self.colors['grid'],
            figcolor=self.colors['bg'],
            facecolor=self.colors['bg'],
            edgecolor=self.colors['text'],
            textcolor=self.colors['text']
        )
        
        # Prepare subplots
        num_plots = 2  # Price and volume by default
        if indicators:
            num_plots += len(indicators)
        
        # Create plot
        fig, axes = mpf.plot(
            df,
            type='candle',
            style=s,
            volume=True,
            figsize=figsize,
            title=title or f'Price Chart with Signals and Predictions',
            returnfig=True,
            panel_ratios=(6, 1) if num_plots == 2 else None,
            warn_too_much_data=10000
        )
        
        fig = axes[0]
        ax1 = axes[1]  # Main price chart
        
        # Add signals if provided
        if signals:
            self._add_signals_to_chart(ax1, df, signals)
        
        # Add predictions if provided
        if predictions is not None:
            self._add_predictions_to_chart(ax1, df, predictions)
        
        # Add support/resistance levels if provided
        if support_resistance:
            self._add_support_resistance_to_chart(ax1, support_resistance)
        
        # Add indicators if provided
        if indicators:
            self._add_indicators_to_chart(axes, df, indicators)
        
        # Adjust layout and save/show
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Chart saved to {save_path}")
        
        if show:
            plt.show()
        
        return fig
    
    def _add_signals_to_chart(self, ax, df, signals):
        """Add trading signals to the chart."""
        for signal in signals:
            if not hasattr(signal, 'timestamp') or signal.timestamp is None:
                continue
            try:
                
            # Find the index position for the signal
                if isinstance(signal.timestamp, str):
                    signal.timestamp = pd.to_datetime(signal.timestamp)
                
                idx = df.index.get_indexer([signal.timestamp], method='nearest')[0]
                if idx < 0 or idx >= len(df):
                    continue
                
                price = df.iloc[idx]['close']
                
                # Plot signal marker
                if signal.direction.lower() == 'buy':
                    ax.scatter(idx, price * 0.99, s=120, marker='^', 
                              color=self.colors['signal_buy'], zorder=5)
                elif signal.direction.lower() == 'sell':
                    ax.scatter(idx, price * 1.01, s=120, marker='v', 
                              color=self.colors['signal_sell'], zorder=5)
                
                # Add confidence annotation if available
                if hasattr(signal, 'confidence') and signal.confidence is not None:
                    ax.annotate(f"{signal.confidence:.0f}%", 
                               (idx, price * (0.98 if signal.direction.lower() == 'buy' else 1.02)),
                               xytext=(0, 10 if signal.direction.lower() == 'buy' else -10),
                               textcoords='offset points',
                               ha='center', va='center',
                               fontsize=8, fontweight='bold',
                               color=self.colors['text'],
                               bbox=dict(boxstyle='round,pad=0.3', fc=self.colors['bg'], alpha=0.7))
            except Exception as e:
                logger.error(f"Error plotting signal: {e}")
    
    def _add_predictions_to_chart(self, ax, df, predictions):
        """Add price predictions to the chart."""
        try:
            # Ensure predictions align with df
            if isinstance(predictions, pd.DataFrame):
                # If predictions is a DataFrame with predicted prices
                if len(predictions) != len(df):
                    logger.warning("Predictions length doesn't match data length")
                    return
                
                # Plot prediction line
                ax.plot(range(len(df)), predictions['predicted_price'], 
                       color=self.colors['prediction'], linewidth=1.5, 
                       linestyle='--', label='Predicted Price')
                
                # Plot confidence intervals if available
                if 'upper_bound' in predictions.columns and 'lower_bound' in predictions.columns:
                    ax.fill_between(
                        range(len(df)),
                        predictions['lower_bound'],
                        predictions['upper_bound'],
                        color=self.colors['confidence'],
                        alpha=0.2,
                        label='Prediction Interval'
                    )
            else:
                # If predictions is a simple array or list
                ax.plot(range(len(df)), predictions, 
                       color=self.colors['prediction'], linewidth=1.5, 
                       linestyle='--', label='Predicted Price')
            
            ax.legend(loc='upper left')
            
        except Exception as e:
            logger.error(f"Error plotting predictions: {e}")
    
    def _add_support_resistance_to_chart(self, ax, support_resistance):
        """Add support and resistance levels to the chart."""
        try:
            # Add support levels
            if 'support' in support_resistance and support_resistance['support']:
                for level in support_resistance['support']:
                    ax.axhline(y=level, color=self.colors['support'], 
                              linestyle='--', linewidth=1, alpha=0.7)
                    ax.annotate(f"S: {level:.5f}", xy=(0, level), xytext=(-40, 0),
                               textcoords='offset points', fontsize=8,
                               color=self.colors['support'])
            
            # Add resistance levels
            if 'resistance' in support_resistance and support_resistance['resistance']:
                for level in support_resistance['resistance']:
                    ax.axhline(y=level, color=self.colors['resistance'], 
                              linestyle='--', linewidth=1, alpha=0.7)
                    ax.annotate(f"R: {level:.5f}", xy=(0, level), xytext=(-40, 0),
                               textcoords='offset points', fontsize=8,
                               color=self.colors['resistance'])
        except Exception as e:
            logger.error(f"Error plotting support/resistance: {e}")
    
    def _add_indicators_to_chart(self, axes, df, indicators):
        """Add technical indicators to the chart."""
        try:
            main_ax = axes[1]  # Main price chart
            
            # Plot indicators on the main chart
            for name, values in indicators.items():
                if name.lower() in ['ma', 'ema', 'sma', 'wma', 'moving average']:
                    # Plot moving averages on the main chart
                    if isinstance(values, dict):
                        for period, data in values.items():
                            main_ax.plot(range(len(df)), data, 
                                       label=f"{name.upper()} {period}")
                    else:
                        main_ax.plot(range(len(df)), values, label=name.upper())
                
                elif name.lower() in ['bollinger', 'bands', 'bollinger bands']:
                    # Plot Bollinger Bands
                    if isinstance(values, dict) and 'middle' in values and 'upper' in values and 'lower' in values:
                        main_ax.plot(range(len(df)), values['middle'], color='#9e9e9e', label='BB Middle')
                        main_ax.plot(range(len(df)), values['upper'], color='#7cb342', label='BB Upper')
                        main_ax.plot(range(len(df)), values['lower'], color='#7cb342', label='BB Lower')
                        main_ax.fill_between(range(len(df)), values['lower'], values['upper'], 
                                           color='#7cb342', alpha=0.1)
                
                # Add more indicators as needed
            
            main_ax.legend(loc='upper left')
            
        except Exception as e:
            logger.error(f"Error plotting indicators: {e}")
    
    def plot_equity_curve(self, performance_data, title=None, save_path=None, show=True, figsize=(12, 6)):
        """
        Plot equity curve from performance data.
        
        Args:
            performance_data: DataFrame or dict with performance metrics
            title: Chart title
            save_path: Path to save the chart image
            show: Whether to display the chart
            figsize: Figure size tuple
            
        Returns:
            matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if isinstance(performance_data, pd.DataFrame):
            if 'equity' in performance_data.columns:
                equity = performance_data['equity']
                dates = performance_data.index
            else:
                logger.error("Performance data doesn't contain 'equity' column")
                return None
        elif isinstance(performance_data, dict) and 'equity_curve' in performance_data:
            equity = performance_data['equity_curve']
            dates = range(len(equity))
        else:
            logger.error("Invalid performance data format")
            return None
        
        # Plot equity curve
        ax.plot(dates, equity, color=self.colors['up'], linewidth=2)
        
        # Add drawdown shading
        self._add_drawdown_shading(ax, equity, dates)
        
        # Set title and labels
        ax.set_title(title or 'Equity Curve', fontsize=14)
        ax.set_xlabel('Date' if isinstance(dates, pd.DatetimeIndex) else 'Trade Number')
        ax.set_ylabel('Equity')
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Add key metrics if available
        self._add_performance_metrics(ax, performance_data)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Equity curve saved to {save_path}")
        
        if show:
            plt.show()
        
        return fig
    
    def _add_drawdown_shading(self, ax, equity, dates):
        """Add drawdown shading to the equity curve."""
        try:
            # Calculate running maximum
            running_max = pd.Series(equity).cummax()
            
            # Calculate drawdowns
            drawdowns = (equity - running_max) / running_max * 100
            
            # Find drawdown periods
            is_drawdown = drawdowns < 0
            
            # Shade drawdown periods
            for i in range(1, len(is_drawdown)):
                if is_drawdown.iloc[i] and not is_drawdown.iloc[i-1]:
                    start_idx = i
                elif not is_drawdown.iloc[i] and is_drawdown.iloc[i-1]:
                    end_idx = i
                    # Shade this drawdown period
                    ax.axvspan(dates[start_idx], dates[end_idx], 
                              color='red', alpha=0.2, zorder=0)
        except Exception as e:
            logger.error(f"Error adding drawdown shading: {e}")
    
    def _add_performance_metrics(self, ax, performance_data):
        """Add key performance metrics to the chart."""
        try:
            metrics = {}
            
            if isinstance(performance_data, dict):
                # Extract metrics from dict
                metrics = {
                    'Net Profit': f"{performance_data.get('net_profit', 'N/A')}",
                    'Win Rate': f"{performance_data.get('win_rate', 0) * 100:.1f}%" if 'win_rate' in performance_data else 'N/A',
                    'Max Drawdown': f"{performance_data.get('max_drawdown', 0) * 100:.1f}%" if 'max_drawdown' in performance_data else 'N/A',
                    'Profit Factor': f"{performance_data.get('profit_factor', 'N/A')}"
                }
            elif isinstance(performance_data, pd.DataFrame) and 'metrics' in performance_data:
                # Extract metrics from DataFrame
                metrics = performance_data['metrics'].iloc[-1].to_dict()
            
            if metrics:
                # Create text box with metrics
                textstr = '\n'.join([f"{k}: {v}" for k, v in metrics.items() if v != 'N/A'])
                props = dict(boxstyle='round', facecolor=self.colors['bg'], alpha=0.7)
                ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
                       verticalalignment='top', bbox=props)
        except Exception as e:
            logger.error(f"Error adding performance metrics: {e}")
    
    def save_figure(self, fig, path):
        """Save figure to file."""
        try:
            fig.savefig(path, dpi=300, bbox_inches='tight')
            logger.info(f"Figure saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving figure: {e}")
            return False
