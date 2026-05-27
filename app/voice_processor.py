import os
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self):
        self.asr_model = None
        self.tts_client = None
        self._initialized = False
    
    async def initialize(self):
        try:
            from speechbrain.inference.ASR import EncoderDecoderASR
            self.asr_model = EncoderDecoderASR.from_hparams(
                source="speechbrain/asr-crdnn-rnnlm-librispeech",
                savedir="pretrained_models/asr",
                run_opts={"device": "cpu"}
            )
            logger.info("✅ ASR модель загружена")
        except Exception as e:
            logger.warning(f"ASR недоступна: {e}")
        
        try:
            from google.cloud import texttospeech
            self.tts_client = texttospeech.TextToSpeechClient()
            logger.info("✅ TTS клиент готов")
        except Exception as e:
            logger.warning(f"TTS недоступен: {e}")
        
        self._initialized = True
    
    async def download_voice(self, bot, file_id):
        try:
            file = await bot.get_file(file_id)
            temp_dir = tempfile.gettempdir()
            voice_path = Path(temp_dir) / f"voice_{file_id}.ogg"
            await file.download_to_drive(voice_path)
            return str(voice_path)
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    async def transcribe(self, file_path):
        if not self.asr_model:
            return None
        try:
            transcript = self.asr_model.transcribe_file(file_path)
            return transcript.strip()
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    async def synthesize_speech(self, text):
        if not self.tts_client:
            return None
        try:
            from google.cloud import texttospeech
            
            synthesis_input = texttospeech.SynthesisInput(text=text[:500])
            voice = texttospeech.VoiceSelectionParams(
                language_code="ru-RU",
                name="ru-RU-Wavenet-D",
                ssml_gender=texttospeech.SsmlVoiceGender.MALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.OGG_OPUS,
                speaking_rate=0.95
            )
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            return response.audio_content
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
    
    def is_available(self):
        return self.asr_model is not None

voice_processor = VoiceProcessor()
