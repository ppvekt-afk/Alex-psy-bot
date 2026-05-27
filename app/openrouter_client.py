import aiohttp
import asyncio
import logging
import re
import ssl
from typing import List, Dict, Optional
from app.config import config

logger = logging.getLogger(__name__)

class OpenRouterClient:
    def __init__(self):
        self.api_key = None
        self.model = None
        self._session = None

    async def initialize(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.model = config.OPENROUTER_MODEL
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(connector=connector)
        logger.info(f"OpenRouter client ready, model: {self.model}")

    async def _get_session(self):
        if self._session is None:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'[&<>]', '', text)
        return text.strip()

    async def generate_response(self, user_message: str, history: List[Dict]) -> str:
        system_prompt = """Ты Александр, клинический психолог. Отвечай спокойно, по делу, без маркдауна и спецсимволов. Будь полезным и эмпатичным."""

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-5:])
        messages.append({"role": "user", "content": user_message})

        session = await self._get_session()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }

        try:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    raw = data["choices"][0]["message"]["content"]
                    cleaned = self._clean_text(raw)
                    if cleaned and len(cleaned) > 10:
                        return cleaned
                    else:
                        return "Пожалуйста, переформулируй вопрос."
                else:
                    return "Извини, сейчас не могу ответить. Попробуй ещё раз."
        except Exception as e:
            logger.error(f"Error: {e}")
            return "Извини, технические неполадки. Попробуй позже."

    async def close(self):
        if self._session:
            await self._session.close()

openrouter_client = OpenRouterClient()
