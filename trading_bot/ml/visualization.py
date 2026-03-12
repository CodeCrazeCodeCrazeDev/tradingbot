import logging
logger = logging.getLogger(__name__)
from pathlib import Path
"""Visualization tools for ML model outputs.

This module provides visualization utilities for displaying and analyzing
outputs from various ML models in the trading bot, including price predictions,
feature importance, model performance metrics, and attention patterns.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from loguru import logger
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Set
import pathlib
import numpy
import pandas


class ModelVisualizer:
    """Visualization tools for ML model outputs."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the model visualizer.
        
        Args:
            output_dir: Directory to save visualizations. If None, plots will be shown
                       but not saved automatically.
        """
        self.output_dir = output_dir
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        
        # Set default style
        sns.set_style('whitegrid')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 12
        
        logger.info("ModelVisualizer initialized")
    
    def plot_price_predictions(self, df: pd.DataFrame, predictions: Dict[str, float], 
                              lookback_periods: int = 30, title: Optional[str] = None,
                              save_path: Optional[str] = None) -> Figure:
        """Plot historical prices and future predictions.
        
        Args:
            df: DataFrame with historical price data
            predictions: Dictionary with predictions for different horizons
            lookback_periods: Number of historical periods to show
            title: Custom title for the plot
            save_path: Path to save the figure (if None, uses output_dir)
            
        Returns:
            Matplotlib Figure object
        """
        try:
            # Extract historical data
            historical_data = df['close'].iloc[-lookback_periods:]
            
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot historical data
            ax.plot(historical_data.index, historical_data.values, 
                   label='Historical', color='blue', linewidth=2)
            
            # Get the last date from historical data
            last_date = historical_data.index[-1]
            
            # Create future dates based on the prediction horizons
            future_dates = pd.date_range(
                start=last_date, 
                periods=len(predictions) + 1
            )[1:]
            
            # Extract prediction values in order
            horizons = sorted(predictions.keys(), key=lambda x: int(x.replace('t+', '')))
            prediction_values = [predictions[h] for h in horizons]
            
            # Plot predictions
            ax.plot(future_dates, prediction_values, 
                   label='Predictions', color='red', linestyle='--', linewidth=2, marker='o')
            
            # Add confidence interval if available
            if 'lower_bound' in predictions and 'upper_bound' in predictions:
                lower_bounds = [predictions[f'lower_bound_{h}'] for h in horizons]
                upper_bounds = [predictions[f'upper_bound_{h}'] for h in horizons]
                ax.fill_between(future_dates, lower_bounds, upper_bounds, 
                               color='red', alpha=0.2, label='Confidence Interval')
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.xticks(rotation=45)
            
            # Add labels and title
            ax.set_xlabel('Date')
            ax.set_ylabel('Price')
            ax.set_title(title or 'Price Predictions')
            
            # Add legend
            ax.legend()
            
            # Add grid
            ax.grid(True, alpha=0.3)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save figure if path is provided
            if save_path or self.output_dir:
                path = save_path or os.path.join(self.output_dir, 'price_predictions.png')
                plt.savefig(path, dpi=300, bbox_inches='tight')
                logger.info(f"Price prediction plot saved to {path}")
            
            return fig
            
        except Exception as e:
            logger.error(f"Error plotting price predictions: {e}")
            # Return empty figure in case of error
            return plt.figure()
    
    def plot_feature_importance(self, feature_scores: Dict[str, float], 
                               top_n: int = 10, title: Optional[str] = None,
                               save_path: Optional[str] = None) -> Figure:
        """Plot feature importance scores.
        
        Args:
            feature_scores: Dictionary mapping feature names to importance scores
            top_n: Number of top features to display
            title: Custom title for the plot
            save_path: Path to save the figure (if None, uses output_dir)
            
        Returns:
            Matplotlib Figure object
        """
        try:
            # Sort features by importance
            sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Select top N features
            top_features = sorted_features[:top_n]
            
            # Create DataFrame for plotting
            df_plot = pd.DataFrame(top_features, columns=['Feature', 'Importance'])
            
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create horizontal bar plot
            sns.barplot(x='Importance', y='Feature', data=df_plot, palette='viridis', ax=ax)
            
            # Add labels and title
            ax.set_xlabel('Importance Score')
            ax.set_ylabel('Feature')
            ax.set_title(title or 'Feature Importance Analysis')
            
            # Add value labels to bars
            for i, v in enumerate(df_plot['Importance']):
                ax.text(v + 0.01, i, f'{v:.4f}', va='center')
            
            # Adjust layout
            plt.tight_layout()
            
            # Save figure if path is provided
            if save_path or self.output_dir:
                path = save_path or os.path.join(self.output_dir, 'feature_importance.png')
                plt.savefig(path, dpi=300, bbox_inches='tight')
                logger.info(f"Feature importance plot saved to {path}")
            
            return fig
            
        except Exception as e:
            logger.error(f"Error plotting feature importance: {e}")
            # Return empty figure in case of error
            return plt.figure()
    
    def plot_performance_metrics(self, metrics: Dict[str, float], 
                                title: Optional[str] = None,
                                save_path: Optional[str] = None) -> Figure:
        """Plot model performance metrics.
        
        Args:
            metrics: Dictionary with performance metrics
            title: Custom title for the plot
            save_path: Path to save the figure (if None, uses output_dir)
            
        Returns:
            Matplotlib Figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create bar plot
            metrics_items = list(metrics.items())
            x = [item[0].upper() for item in metrics_items]
            y = [item[1] for item in metrics_items]
            
            bars = ax.bar(x, y, color=sns.color_palette('viridis', len(metrics)))
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{height:.4f}', ha='center', va='bottom')
            
            # Add labels and title
            ax.set_xlabel('Metric')
            ax.set_ylabel('Value')
            ax.set_title(title or 'Model Performance Metrics')
            
            # Adjust layout
            plt.tight_layout()
            
            # Save figure if path is provided
            if save_path or self.output_dir:
                path = save_path or os.path.join(self.output_dir, 'performance_metrics.png')
                plt.savefig(path, dpi=300, bbox_inches='tight')
                logger.info(f"Performance metrics plot saved to {path}")
            
            return fig
            
        except Exception as e:
            logger.error(f"Error plotting performance metrics: {e}")
            # Return empty figure in case of error
            return plt.figure()
    
    def plot_training_history(self, history: Dict[str, List[float]], 
                             title: Optional[str] = None,
                             save_path: Optional[str] = None) -> Figure:
        """Plot model training history.
        
        Args:
            history: Dictionary with training metrics (e.g., loss, val_loss)
            title: Custom title for the plot
            save_path: Path to save the figure (if None, uses output_dir)
            
        Returns:
            Matplotlib Figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot each metric
            for metric_name, values in history.items():
                if isinstance(values, list) and len(values) > 0:
                    ax.plot(range(1, len(values) + 1), values, label=metric_name)
            
            # Add labels and title
            ax.set_xlabel('Epoch')
            ax.set_ylabel('Value')
            ax.set_title(title or 'Training History')
            
            # Add legend
            ax.legend()
            
            # Add grid
            ax.grid(True, alpha=0.3)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save figure if path is provided
            if save_path or self.output_dir:
                path = save_path or os.path.join(self.output_dir, 'training_history.png')
                plt.savefig(path, dpi=300, bbox_inches='tight')
                logger.info(f"Training history plot saved to {path}")
            
            return fig
            
        except Exception as e:
            logger.error(f"Error plotting training history: {e}")
            # Return empty figure in case of error
            return plt.figure()
    
    def plot_attention_heatmap(self, attention_weights: np.ndarray, 
                              feature_names: List[str],
                              title: Optional[str] = None,
                              save_path: Optional[str] = None) -> Figure:
        """Plot attention weights as a heatmap.
        
        Args:
            attention_weights: 2D array of attention weights
            feature_names: List of feature names
            title: Custom title for the plot
            save_path: Path to save the figure (if None, uses output_dir)
            
        Returns:
            Matplotlib Figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Create heatmap
            sns.heatmap(attention_weights, annot=True, fmt=".2f", 
                       xticklabels=feature_names, 
                       yticklabels=feature_names,
                       cmap="YlGnBu", ax=ax)
            
            # Add title
            ax.set_title(title or 'Attention Weights Heatmap')
            
            # Adjust layout
            plt.tight_layout()
            
            # Save figure if path is provided
            if save_path or self.output_dir:
                path = save_path or os.path.join(self.output_dir, 'attention_heatmap.png')
                plt.savefig(path, dpi=300, bbox_inches='tight')
                logger.info(f"Attention heatmap saved to {path}")
            
            return fig
            
        except Exception as e:
            logger.error(f"Error plotting attention heatmap: {e}")
            # Return empty figure in case of error
            return plt.figure()
    
    def plot_confusion_matrix(self, cm: np.ndarray, class_names: List[str],
                             title: Optional[str] = None,
                             save_path: Optional[str] = None) -> Figure:
        """Plot confusion matrix for classification results.
        
        Args:
            cm: Confusion matrix as numpy array
            class_names: List of class names
            title: Custom title for the plot
            save_path: Path to save the figure (if None, uses output_dir)
            
        Returns:
            Matplotlib Figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Create heatmap
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                       xticklabels=class_names, yticklabels=class_names, ax=ax)
            
            # Add labels and title
            ax.set_xlabel('Predicted')
            ax.set_ylabel('Actual')
            ax.set_title(title or 'Confusion Matrix')
            
            # Adjust layout
            plt.tight_layout()
            
            # Save figure if path is provided
            if save_path or self.output_dir:
                path = save_path or os.path.join(self.output_dir, 'confusion_matrix.png')
                plt.savefig(path, dpi=300, bbox_inches='tight')
                logger.info(f"Confusion matrix saved to {path}")
            
            return fig
            
        except Exception as e:
            logger.error(f"Error plotting confusion matrix: {e}")
            # Return empty figure in case of error
            return plt.figure()
    
    def plot_roc_curve(self, fpr: np.ndarray, tpr: np.ndarray, auc: float,
                      title: Optional[str] = None,
                      save_path: Optional[str] = None) -> Figure:
        """Plot ROC curve for binary classification.
        
        Args:
            fpr: False positive rates
            tpr: True positive rates
            auc: Area under the curve
            title: Custom title for the plot
            save_path: Path to save the figure (if None, uses output_dir)
            
        Returns:
            Matplotlib Figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Plot ROC curve
            ax.plot(fpr, tpr, color='blue', lw=2, label=f'ROC curve (AUC = {auc:.3f})')
            ax.plot([0, 1], [0, 1], color='gray', linestyle='--')
            
            # Add labels and title
            ax.set_xlabel('False Positive Rate')
            ax.set_ylabel('True Positive Rate')
            ax.set_title(title or 'Receiver Operating Characteristic')
            
            # Set axis limits
            ax.set_xlim([0.0, 1.0])
            ax.set_ylim([0.0, 1.05])
            
            # Add legend
            ax.legend(loc="lower right")
            
            # Adjust layout
            plt.tight_layout()
            
            # Save figure if path is provided
            if save_path or self.output_dir:
                path = save_path or os.path.join(self.output_dir, 'roc_curve.png')
                plt.savefig(path, dpi=300, bbox_inches='tight')
                logger.info(f"ROC curve saved to {path}")
            
            return fig
            
        except Exception as e:
            logger.error(f"Error plotting ROC curve: {e}")
            # Return empty figure in case of error
            return plt.figure()
    
    def plot_ensemble_comparison(self, predictions: Dict[str, List[float]], 
                                actual: List[float], dates: List[Any],
                                title: Optional[str] = None,
                                save_path: Optional[str] = None) -> Figure:
        """Plot comparison of ensemble model predictions.
        
        Args:
            predictions: Dictionary mapping model names to lists of predictions
            actual: List of actual values
            dates: List of dates or x-axis values
            title: Custom title for the plot
            save_path: Path to save the figure (if None, uses output_dir)
            
        Returns:
            Matplotlib Figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot actual values
            ax.plot(dates, actual, label='Actual', color='black', linewidth=2)
            
            # Plot predictions for each model
            colors = plt.cm.tab10.colors
            for i, (model_name, preds) in enumerate(predictions.items()):
                color = colors[i % len(colors)]
                ax.plot(dates, preds, label=model_name, color=color, alpha=0.7)
            
            # Format x-axis if dates
            if isinstance(dates[0], (pd.Timestamp, np.datetime64)):
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.xticks(rotation=45)
            
            # Add labels and title
            ax.set_xlabel('Time')
            ax.set_ylabel('Value')
            ax.set_title(title or 'Ensemble Model Comparison')
            
            # Add legend
            ax.legend(loc='best')
            
            # Add grid
            ax.grid(True, alpha=0.3)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save figure if path is provided
            if save_path or self.output_dir:
                path = save_path or os.path.join(self.output_dir, 'ensemble_comparison.png')
                plt.savefig(path, dpi=300, bbox_inches='tight')
                logger.info(f"Ensemble comparison plot saved to {path}")
            
            return fig
            
        except Exception as e:
            logger.error(f"Error plotting ensemble comparison: {e}")
            # Return empty figure in case of error
            return plt.figure()
    
    def plot_model_weights(self, weights: Dict[str, float], 
                          title: Optional[str] = None,
                          save_path: Optional[str] = None) -> Figure:
        """Plot model weights in an ensemble.
        
        Args:
            weights: Dictionary mapping model names to weights
            title: Custom title for the plot
            save_path: Path to save the figure (if None, uses output_dir)
            
        Returns:
            Matplotlib Figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                weights.values(), 
                labels=weights.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=plt.cm.tab10.colors[:len(weights)]
            )
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')
            
            # Add title
            ax.set_title(title or 'Ensemble Model Weights')
            
            # Adjust layout
            plt.tight_layout()
            
            # Save figure if path is provided
            if save_path or self.output_dir:
                path = save_path or os.path.join(self.output_dir, 'model_weights.png')
                plt.savefig(path, dpi=300, bbox_inches='tight')
                logger.info(f"Model weights plot saved to {path}")
            
            return fig
            
        except Exception as e:
            logger.error(f"Error plotting model weights: {e}")
            # Return empty figure in case of error
            return plt.figure()
    
    def create_dashboard(self, plots: Dict[str, Figure], 
                        layout: Optional[Tuple[int, int]] = None,
                        title: str = "ML Model Dashboard",
                        save_path: Optional[str] = None) -> Figure:
        """Create a dashboard with multiple plots.
        
        Args:
            plots: Dictionary mapping plot names to Figure objects
            layout: Tuple of (rows, cols) for dashboard layout
                   If None, will be calculated automatically
            title: Dashboard title
            save_path: Path to save the figure (if None, uses output_dir)
            
        Returns:
            Matplotlib Figure object
        """
        try:
            # Determine layout if not provided
            n_plots = len(plots)
            if layout is None:
                cols = min(3, n_plots)
                rows = (n_plots + cols - 1) // cols  # Ceiling division
            else:
                rows, cols = layout
            
            # Create figure
            fig = plt.figure(figsize=(cols * 6, rows * 5))
            fig.suptitle(title, fontsize=16)
            
            # Add each plot as a subplot
            for i, (plot_name, plot_fig) in enumerate(plots.items(), 1):
                # Create subplot
                ax = fig.add_subplot(rows, cols, i)
                
                # Get the figure canvas and convert to image
                plot_fig.canvas.draw()
                img = np.array(plot_fig.canvas.renderer.buffer_rgba())
                
                # Display the image
                ax.imshow(img)
                ax.set_title(plot_name)
                ax.axis('off')
                
                # Close the original figure to free memory
                plt.close(plot_fig)
            
            # Adjust layout
            plt.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for suptitle
            
            # Save figure if path is provided
            if save_path or self.output_dir:
                path = save_path or os.path.join(self.output_dir, 'dashboard.png')
                plt.savefig(path, dpi=300, bbox_inches='tight')
                logger.info(f"Dashboard saved to {path}")
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            # Return empty figure in case of error
            return plt.figure()
