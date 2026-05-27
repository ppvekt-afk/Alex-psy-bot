import asyncio
import logging
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

async def main():
    logger.info("Запуск Александра с голосовыми возможностями...")
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
    
    logger.info("✅ Бот запущен! Голосовые сообщения поддерживаются.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
