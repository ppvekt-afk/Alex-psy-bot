#!/usr/bin/env python3
import asyncio
import threading
import time
import logging
from flask import Flask, jsonify
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app.config import config
from app.handlers import router
from app.voice_handlers import router as voice_router
from app.openrouter_client import openrouter_client
from app.voice_processor import voice_processor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return jsonify({"status": "alive", "service": "alexander-psychologist-bot"})

def run_flask():
    """Запускает Flask-сервер для health-check Render."""
    logger.info("Запуск Flask health check сервера на порту 10000...")
    flask_app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)

async def main():
    logger.info("Запуск Александра (психолог)...")
    config.validate()
    await openrouter_client.initialize()
    await voice_processor.initialize()

    bot = Bot(
        token=config.TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=None)
    )
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(voice_router)

    logger.info("✅ Александр запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Даем время Flask запуститься
    time.sleep(2)

    # Запускаем бота
    asyncio.run(main())
