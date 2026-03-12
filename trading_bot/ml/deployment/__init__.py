"""
deployment package
"""

try:
    from .batch_inference import BatchInference, create_batch_inference
    from .onnx_converter import OnnxConverter, create_onnx_converter
    from .quantizer import Quantizer, create_quantizer
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in deployment: {e}')

__all__ = [
    'BatchInference',
    'OnnxConverter',
    'Quantizer',
    'create_batch_inference',
    'create_onnx_converter',
    'create_quantizer',
]