import logging
import os
import re
from aiogram import Router, F
from aiogram.types import Message
from io import BytesIO

from app.voice_processor import voice_processor
from app.openrouter_client import openrouter_client
from app.handlers import get_history, update_history

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.voice)
async def handle_voice_message(message: Message):
    user_id = message.from_user.id
    
    if not voice_processor.is_available():
        await message.answer("Голосовые сообщения временно недоступны. Напишите текстом.")
        return
    
    status_msg = await message.answer("Распознаю голосовое сообщение...")
    
    voice_path = await voice_processor.download_voice(message.bot, message.voice.file_id)
    
    if not voice_path:
        await status_msg.edit_text("Не удалось загрузить голосовое сообщение.")
        return
    
    transcript = await voice_processor.transcribe(voice_path)
    
    if transcript:
        await status_msg.edit_text(f"Распознанный текст:\n{transcript}\n\nФормирую ответ...")
        
        history = await get_history(user_id)
        response = await openrouter_client.generate_response(transcript, history)
        await update_history(user_id, transcript, response)
        
        response = re.sub(r'\*\*(.+?)\*\*', r'\1', response)
        response = re.sub(r'\*(.+?)\*', r'\1', response)
        
        await status_msg.edit_text(f"Вы сказали: {transcript}\n\n{response}")
        
        audio_response = await voice_processor.synthesize_speech(response[:500])
        if audio_response:
            audio_file = BytesIO(audio_response)
            audio_file.name = "response.ogg"
            await message.reply_voice(voice=audio_file)
        
        os.unlink(voice_path)
    else:
        await status_msg.edit_text("Не удалось распознать речь. Попробуйте говорить чётче.")

@router.message(F.text & (F.text.lower().contains("озвучь") | F.text.lower().contains("скажи")))
async def handle_text_to_speech(message: Message):
    text = message.text
    text = re.sub(r'(озвучь|скажи|прочитай)', '', text, flags=re.IGNORECASE).strip()
    
    if not text:
        await message.answer("Что озвучить? Напишите текст после команды.")
        return
    
    status_msg = await message.answer("Озвучиваю...")
    
    audio_data = await voice_processor.synthesize_speech(text[:500])
    
    if audio_data:
        audio_file = BytesIO(audio_data)
        audio_file.name = "response.ogg"
        await message.reply_voice(voice=audio_file)
        await status_msg.delete()
    else:
        await status_msg.edit_text("Не удалось озвучить текст.")
