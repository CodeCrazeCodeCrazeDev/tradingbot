import logging
logger = logging.getLogger(__name__)
from pathlib import Path
"""
ML visualization module for the trading bot.

This module provides tools for visualizing ML model predictions,
feature importance, and model performance metrics.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve
import shap
from loguru import logger
from typing import List
import pathlib
import numpy
import pandas
from typing import Set


class MLVisualizer:
    """
    Visualizes ML model predictions, feature importance, and performance metrics.
    
    This class provides methods to create visualizations that help understand
    ML model behavior, predictions, and performance in the trading context.
    """
    
    def __init__(self, theme='dark'):
        """
        Initialize the ML visualizer.
        
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
                'primary': '#42a5f5',
                'secondary': '#ff7043',
                'positive': '#26a69a',
                'negative': '#ef5350',
                'neutral': '#bdbdbd',
                'highlight': '#ffeb3b'
            }
        elif self.theme == 'light':
            plt.style.use('default')
            self.colors = {
                'bg': '#ffffff',
                'text': '#212121',
                'grid': '#e0e0e0',
                'primary': '#1e88e5',
                'secondary': '#f4511e',
                'positive': '#26a69a',
                'negative': '#ef5350',
                'neutral': '#9e9e9e',
                'highlight': '#fdd835'
            }
        else:
            plt.style.use('default')
            self.colors = {
                'bg': '#ffffff',
                'text': '#212121',
                'grid': '#e0e0e0',
                'primary': '#1e88e5',
                'secondary': '#f4511e',
                'positive': '#26a69a',
                'negative': '#ef5350',
                'neutral': '#9e9e9e',
                'highlight': '#fdd835'
            }
    
    def plot_feature_importance(self, model, feature_names, title=None, 
                               top_n=20, save_path=None, show=True, figsize=(10, 8)):
        """
        Plot feature importance from a trained model.
        
        Args:
            model: Trained model with feature_importances_ attribute
            feature_names: List of feature names
            title: Chart title
            top_n: Number of top features to show
            save_path: Path to save the chart image
            show: Whether to display the chart
            figsize: Figure size tuple
            
        Returns:
            matplotlib figure object
        """
        try:
            # Get feature importance
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importances = np.abs(model.coef_[0])
            else:
                logger.error("Model doesn't have feature_importances_ or coef_ attribute")
                return None
            
            # Create DataFrame for plotting
            feature_importance = pd.DataFrame({
                'Feature': feature_names,
                'Importance': importances
            })
            
            # Sort by importance and take top N
            feature_importance = feature_importance.sort_values('Importance', ascending=False).head(top_n)
            
            # Create plot
            fig, ax = plt.subplots(figsize=figsize)
            sns.barplot(x='Importance', y='Feature', data=feature_importance, 
                       palette=[self.colors['primary']], ax=ax)
            
            # Set title and labels
            ax.set_title(title or 'Feature Importance', fontsize=14)
            ax.set_xlabel('Importance')
            ax.set_ylabel('Feature')
            
            # Add grid
            ax.grid(True, axis='x', alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Feature importance plot saved to {save_path}")
            
            if show:
                plt.show()
            
            return fig
        
        except Exception as e:
            logger.error(f"Error plotting feature importance: {e}")
            return None
    
    def plot_shap_values(self, model, X, feature_names=None, sample_size=100, 
                        plot_type='summary', title=None, save_path=None, show=True, figsize=(12, 8)):
        """
        Plot SHAP values to explain model predictions.
        
        Args:
            model: Trained model
            X: Feature matrix
            feature_names: List of feature names
            sample_size: Number of samples to use for SHAP calculation
            plot_type: Type of SHAP plot ('summary', 'bar', 'waterfall', 'force')
            title: Chart title
            save_path: Path to save the chart image
            show: Whether to display the chart
            figsize: Figure size tuple
            
        Returns:
            matplotlib figure object
        """
        try:
            # Sample data if needed
            if sample_size and sample_size < X.shape[0]:
                X_sample = X.sample(sample_size, random_state=42)
            else:
                X_sample = X
            
            # Create explainer
            if hasattr(model, 'predict_proba'):
                explainer = shap.Explainer(model)
            else:
                explainer = shap.Explainer(model.predict, X_sample)
            
            # Calculate SHAP values
            shap_values = explainer(X_sample)
            
            # Create plot
            plt.figure(figsize=figsize)
            
            if plot_type == 'summary':
                shap.summary_plot(shap_values, X_sample, feature_names=feature_names, show=False)
            elif plot_type == 'bar':
                shap.summary_plot(shap_values, X_sample, feature_names=feature_names, plot_type='bar', show=False)
            elif plot_type == 'waterfall':
                if X_sample.shape[0] > 1:
                    logger.warning("Waterfall plot requires a single sample. Using first sample.")
                shap.waterfall_plot(shap_values[0], show=False)
            elif plot_type == 'force':
                if X_sample.shape[0] > 1:
                    logger.warning("Force plot requires a single sample. Using first sample.")
                shap.force_plot(explainer.expected_value, shap_values[0], X_sample.iloc[0], feature_names=feature_names, show=False)
            
            # Set title
            if title:
                plt.title(title, fontsize=14)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"SHAP plot saved to {save_path}")
            
            if show:
                plt.show()
            
            fig = plt.gcf()
            return fig
        
        except Exception as e:
            logger.error(f"Error plotting SHAP values: {e}")
            return None
    
    def plot_confusion_matrix(self, y_true, y_pred, class_names=None, 
                             title=None, save_path=None, show=True, figsize=(8, 6)):
        """
        Plot confusion matrix for classification results.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            class_names: Names of classes
            title: Chart title
            save_path: Path to save the chart image
            show: Whether to display the chart
            figsize: Figure size tuple
            
        Returns:
            matplotlib figure object
        """
        try:
            # Compute confusion matrix
            cm = confusion_matrix(y_true, y_pred)
            
            # Create plot
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot heatmap
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                       xticklabels=class_names, yticklabels=class_names, ax=ax)
            
            # Set title and labels
            ax.set_title(title or 'Confusion Matrix', fontsize=14)
            ax.set_xlabel('Predicted')
            ax.set_ylabel('True')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Confusion matrix plot saved to {save_path}")
            
            if show:
                plt.show()
            
            return fig
        
        except Exception as e:
            logger.error(f"Error plotting confusion matrix: {e}")
            return None
    
    def plot_roc_curve(self, y_true, y_score, title=None, save_path=None, show=True, figsize=(8, 6)):
        """
        Plot ROC curve for binary classification.
        
        Args:
            y_true: True labels
            y_score: Predicted probabilities
            title: Chart title
            save_path: Path to save the chart image
            show: Whether to display the chart
            figsize: Figure size tuple
            
        Returns:
            matplotlib figure object
        """
        try:
            # Compute ROC curve and ROC area
            fpr, tpr, _ = roc_curve(y_true, y_score)
            roc_auc = auc(fpr, tpr)
            
            # Create plot
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot ROC curve
            ax.plot(fpr, tpr, color=self.colors['primary'],
                   lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
            
            # Plot diagonal line
            ax.plot([0, 1], [0, 1], color=self.colors['neutral'], lw=1, linestyle='--')
            
            # Set title and labels
            ax.set_title(title or 'Receiver Operating Characteristic', fontsize=14)
            ax.set_xlabel('False Positive Rate')
            ax.set_ylabel('True Positive Rate')
            
            # Set limits and grid
            ax.set_xlim([0.0, 1.0])
            ax.set_ylim([0.0, 1.05])
            ax.grid(True, alpha=0.3)
            ax.legend(loc="lower right")
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"ROC curve plot saved to {save_path}")
            
            if show:
                plt.show()
            
            return fig
        
        except Exception as e:
            logger.error(f"Error plotting ROC curve: {e}")
            return None
    
    def plot_precision_recall_curve(self, y_true, y_score, title=None, save_path=None, show=True, figsize=(8, 6)):
        """
        Plot precision-recall curve for binary classification.
        
        Args:
            y_true: True labels
            y_score: Predicted probabilities
            title: Chart title
            save_path: Path to save the chart image
            show: Whether to display the chart
            figsize: Figure size tuple
            
        Returns:
            matplotlib figure object
        """
        try:
            # Compute precision-recall curve
            precision, recall, _ = precision_recall_curve(y_true, y_score)
            pr_auc = auc(recall, precision)
            
            # Create plot
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot precision-recall curve
            ax.plot(recall, precision, color=self.colors['primary'],
                   lw=2, label=f'PR curve (area = {pr_auc:.2f})')
            
            # Set title and labels
            ax.set_title(title or 'Precision-Recall Curve', fontsize=14)
            ax.set_xlabel('Recall')
            ax.set_ylabel('Precision')
            
            # Set limits and grid
            ax.set_xlim([0.0, 1.0])
            ax.set_ylim([0.0, 1.05])
            ax.grid(True, alpha=0.3)
            ax.legend(loc="lower left")
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Precision-recall curve plot saved to {save_path}")
            
            if show:
                plt.show()
            
            return fig
        
        except Exception as e:
            logger.error(f"Error plotting precision-recall curve: {e}")
            return None
    
    def plot_prediction_distribution(self, y_true, y_pred, title=None, save_path=None, show=True, figsize=(10, 6)):
        """
        Plot distribution of predictions vs actual values.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            title: Chart title
            save_path: Path to save the chart image
            show: Whether to display the chart
            figsize: Figure size tuple
            
        Returns:
            matplotlib figure object
        """
        try:
            # Create plot
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot distributions
            sns.kdeplot(y_true, color=self.colors['primary'], label='Actual', ax=ax)
            sns.kdeplot(y_pred, color=self.colors['secondary'], label='Predicted', ax=ax)
            
            # Set title and labels
            ax.set_title(title or 'Prediction Distribution', fontsize=14)
            ax.set_xlabel('Value')
            ax.set_ylabel('Density')
            
            # Add grid and legend
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Prediction distribution plot saved to {save_path}")
            
            if show:
                plt.show()
            
            return fig
        
        except Exception as e:
            logger.error(f"Error plotting prediction distribution: {e}")
            return None
    
    def plot_learning_curve(self, train_sizes, train_scores, test_scores, 
                           title=None, save_path=None, show=True, figsize=(10, 6)):
        """
        Plot learning curve showing model performance vs training size.
        
        Args:
            train_sizes: Array of training sizes
            train_scores: Array of training scores for each size
            test_scores: Array of test scores for each size
            title: Chart title
            save_path: Path to save the chart image
            show: Whether to display the chart
            figsize: Figure size tuple
            
        Returns:
            matplotlib figure object
        """
        try:
            # Calculate mean and std for train and test scores
            train_mean = np.mean(train_scores, axis=1)
            train_std = np.std(train_scores, axis=1)
            test_mean = np.mean(test_scores, axis=1)
            test_std = np.std(test_scores, axis=1)
            
            # Create plot
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot learning curve
            ax.plot(train_sizes, train_mean, color=self.colors['primary'], marker='o',
                   markersize=5, label='Training score')
            ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std,
                           alpha=0.15, color=self.colors['primary'])
            
            ax.plot(train_sizes, test_mean, color=self.colors['secondary'], marker='s',
                   markersize=5, label='Validation score')
            ax.fill_between(train_sizes, test_mean - test_std, test_mean + test_std,
                           alpha=0.15, color=self.colors['secondary'])
            
            # Set title and labels
            ax.set_title(title or 'Learning Curve', fontsize=14)
            ax.set_xlabel('Training Size')
            ax.set_ylabel('Score')
            
            # Add grid and legend
            ax.grid(True, alpha=0.3)
            ax.legend(loc='lower right')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Learning curve plot saved to {save_path}")
            
            if show:
                plt.show()
            
            return fig
        
        except Exception as e:
            logger.error(f"Error plotting learning curve: {e}")
            return None
    
    def plot_prediction_vs_actual(self, y_true, y_pred, title=None, save_path=None, show=True, figsize=(10, 6)):
        """
        Plot predicted vs actual values as a scatter plot.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            title: Chart title
            save_path: Path to save the chart image
            show: Whether to display the chart
            figsize: Figure size tuple
            
        Returns:
            matplotlib figure object
        """
        try:
            # Create plot
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot scatter
            ax.scatter(y_true, y_pred, color=self.colors['primary'], alpha=0.6)
            
            # Plot perfect prediction line
            min_val = min(np.min(y_true), np.min(y_pred))
            max_val = max(np.max(y_true), np.max(y_pred))
            ax.plot([min_val, max_val], [min_val, max_val], color=self.colors['neutral'], 
                   linestyle='--', label='Perfect Prediction')
            
            # Set title and labels
            ax.set_title(title or 'Predicted vs Actual', fontsize=14)
            ax.set_xlabel('Actual')
            ax.set_ylabel('Predicted')
            
            # Add grid and legend
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Prediction vs actual plot saved to {save_path}")
            
            if show:
                plt.show()
            
            return fig
        
        except Exception as e:
            logger.error(f"Error plotting prediction vs actual: {e}")
            return None
    
    def save_figure(self, fig, path):
        """Save figure to file."""
        try:
            fig.savefig(path, dpi=300, bbox_inches='tight')
            logger.info(f"Figure saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving figure: {e}")
            return False
