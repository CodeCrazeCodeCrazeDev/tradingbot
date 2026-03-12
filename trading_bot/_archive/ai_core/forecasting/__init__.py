"""
forecasting package
"""

try:
    from .deepar import Deepar, create_deepar
    from .deepar_model import DeeparModel, create_deepar_model
    from .ensemble import Ensemble, create_ensemble
    from .forecast_ensemble import ForecastEnsemble, create_forecast_ensemble
    from .informer import Informer, create_informer
    from .informer_model import InformerModel, create_informer_model
    from .nbeats import Nbeats, create_nbeats
    from .nbeats_model import NbeatsModel, create_nbeats_model
    from .temporal_fusion_transformer import (
        GatedResidualNetwork,
        InterpretableMultiHeadAttention,
        QuantileLoss,
        TemporalFusionTransformer,
        VariableSelectionNetwork
    )
    from .tft import Tft, create_tft
    from .uncertainty import Uncertainty, create_uncertainty
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in forecasting: {e}')

__all__ = [
    'Deepar',
    'DeeparModel',
    'Ensemble',
    'ForecastEnsemble',
    'GatedResidualNetwork',
    'Informer',
    'InformerModel',
    'InterpretableMultiHeadAttention',
    'Nbeats',
    'NbeatsModel',
    'QuantileLoss',
    'TemporalFusionTransformer',
    'Tft',
    'Uncertainty',
    'VariableSelectionNetwork',
    'create_deepar',
    'create_deepar_model',
    'create_ensemble',
    'create_forecast_ensemble',
    'create_informer',
    'create_informer_model',
    'create_nbeats',
    'create_nbeats_model',
    'create_tft',
    'create_uncertainty',
]