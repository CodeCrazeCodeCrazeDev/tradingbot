"""
Voice Assistant for Trading Bot
Voice commands and text-to-speech feedback
"""

from .voice_controller import (
    VoiceAssistant,
    VoiceCommand,
    VoiceResponse,
    SpeechRecognizer,
    TextToSpeech
)

__all__ = [
    'VoiceAssistant',
    'VoiceCommand',
    'VoiceResponse',
    'SpeechRecognizer',
    'TextToSpeech'
]
