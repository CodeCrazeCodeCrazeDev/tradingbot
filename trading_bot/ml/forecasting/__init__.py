"""
forecasting package
"""

try:
    from .autoformer_model import (
        AutoCorrelation,
        AutoCorrelationLayer,
        Autoformer,
        AutoformerConfig,
        AutoformerDecoder,
        AutoformerEncoder,
        AutoformerForecaster,
        SeriesDecomp
    )
    from .data_loader import DataLoader, create_data_loader
    from .deepar_model import (
        DeepARConfig,
        DeepARModel,
        GaussianLikelihood,
        NegativeBinomialLikelihood,
        StudentTLikelihood
    )
    from .ensemble_forecaster import EnsembleForecaster, create_ensemble_forecaster
    from .informer_model import (
        AttentionLayer,
        Distilling,
        InformerDecoder,
        InformerEncoder,
        InformerModel,
        ProbAttention,
        ProbMask
    )
    from .nbeats_model import (
        GenericBasis,
        NBeatsBlock,
        NBeatsModel,
        NBeatsStack,
        SeasonalityBasis,
        TrendBasis,
        train_nbeats
    )
    from .tft_model import TFTConfig, TFTForecaster, create_sample_data
    from .train_tft import TFTTrainingPipeline, main
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in forecasting: {e}')

__all__ = [
    'AttentionLayer',
    'AutoCorrelation',
    'AutoCorrelationLayer',
    'Autoformer',
    'AutoformerConfig',
    'AutoformerDecoder',
    'AutoformerEncoder',
    'AutoformerForecaster',
    'DataLoader',
    'DeepARConfig',
    'DeepARModel',
    'Distilling',
    'EnsembleForecaster',
    'GaussianLikelihood',
    'GenericBasis',
    'InformerDecoder',
    'InformerEncoder',
    'InformerModel',
    'NBeatsBlock',
    'NBeatsModel',
    'NBeatsStack',
    'NegativeBinomialLikelihood',
    'ProbAttention',
    'ProbMask',
    'SeasonalityBasis',
    'SeriesDecomp',
    'StudentTLikelihood',
    'TFTConfig',
    'TFTForecaster',
    'TFTTrainingPipeline',
    'TrendBasis',
    'create_data_loader',
    'create_ensemble_forecaster',
    'create_sample_data',
    'main',
    'train_nbeats',
]