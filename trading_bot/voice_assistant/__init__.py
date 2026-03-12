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
    'VoiceAssistantOrchestrator',
    'VoiceAssistant',
    'VoiceCommand',
    'VoiceResponse',
    'SpeechRecognizer',
    'TextToSpeech'
]


class VoiceAssistantOrchestrator:
    """Stub for VoiceAssistantOrchestrator."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
