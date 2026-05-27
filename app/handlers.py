import logging
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ChatAction

from app.openrouter_client import openrouter_client

logger = logging.getLogger(__name__)
router = Router()

BOT_USERNAME = "alexanderpsy_bot"
BOT_NAME = "Александр"
BOT_NAMES = ["александр", "саша", "alexander"]

user_histories = {}

GROUNDING_TECHNIQUES = {
    "54321": "Техника заземления 5-4-3-2-1:\n\n• 5 вещей, которые ты видишь\n• 4 вещи, которые чувствуешь телом\n• 3 звука, которые слышишь\n• 2 запаха, которые ощущаешь\n• 1 вкус",
    "breathing": "Квадратное дыхание:\n\nВдох (4 сек) - Пауза (4 сек) - Выдох (4 сек) - Пауза (4 сек)\n\nПовтори 5-10 раз.",
    "body_scan": "Сканирование тела:\n\nМедленно пройдись вниманием по всему телу от макушки до пальцев ног."
}

def is_addressed_to_me(message: Message) -> bool:
    text = message.text or message.caption or ""
    text_lower = text.lower()
    
    if f"@{BOT_USERNAME}" in text:
        return True
    
    for name in BOT_NAMES:
        if name in text_lower:
            return True
    
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_bot:
        if message.reply_to_message.from_user.username == BOT_USERNAME:
            return True
    
    if message.chat.type == "private":
        return True
    
    return False

async def get_history(user_id: int) -> list:
    return user_histories.get(user_id, [])

async def update_history(user_id: int, user_msg: str, bot_msg: str):
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "content": user_msg})
    user_histories[user_id].append({"role": "assistant", "content": bot_msg})
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]

async def clear_history(user_id: int):
    if user_id in user_histories:
        user_histories[user_id] = []

@router.message(Command("start"))
async def cmd_start(message: Message):
    if not is_addressed_to_me(message):
        return
    await clear_history(message.from_user.id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧠 КПТ", callback_data="info_cbt")],
            [InlineKeyboardButton(text="🧘 Техники заземления", callback_data="info_techniques")],
            [InlineKeyboardButton(text="💬 Как общаться", callback_data="info_howto")]
        ]
    )
    welcome = f"🧠 Александр, клинический психолог\n\nПривет, {message.from_user.first_name}!\nЯ здесь, чтобы поддержать и помочь.\n\nРасскажи, что тебя беспокоит."
    await message.answer(welcome, reply_markup=keyboard)

@router.message(Command("help"))
async def cmd_help(message: Message):
    if not is_addressed_to_me(message):
        return
    help_text = "Команды:\n/start - начать\n/reset - сбросить историю\n/help - справка\n/grounding - техники заземления"
    await message.answer(help_text)

@router.message(Command("reset"))
async def cmd_reset(message: Message):
    if not is_addressed_to_me(message):
        return
    await clear_history(message.from_user.id)
    await message.answer("История диалога сброшена.")

@router.message(Command("grounding"))
async def cmd_grounding(message: Message):
    if not is_addressed_to_me(message):
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="5-4-3-2-1", callback_data="grounding_54321")],
            [InlineKeyboardButton(text="Квадратное дыхание", callback_data="grounding_breathing")],
            [InlineKeyboardButton(text="Сканирование тела", callback_data="grounding_body_scan")]
        ]
    )
    await message.answer("Выбери технику заземления:", reply_markup=keyboard)

@router.message(F.text)
async def handle_message(message: Message):
    if not message.text:
        return

    if not is_addressed_to_me(message):
        return

    user_id = message.from_user.id
    user_text = message.text
    user_text = re.sub(f"@{BOT_USERNAME}", "", user_text, flags=re.IGNORECASE)
    for name in BOT_NAMES:
        user_text = re.sub(r'\b' + re.escape(name) + r'\b', "", user_text, flags=re.IGNORECASE)
    user_text = user_text.strip()

    if not user_text:
        await message.answer("Слушаю тебя. Рассказывай.")
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    history = await get_history(user_id)
    response = await openrouter_client.generate_response(user_text, history)
    await update_history(user_id, user_text, response)
    await message.answer(response)

@router.callback_query(F.data == "info_cbt")
async def info_cbt(callback: CallbackQuery):
    await callback.answer()
    text = "КПТ помогает увидеть связь между мыслями, эмоциями и поведением. Хочешь разобрать конкретную ситуацию?"
    await callback.message.answer(text)

@router.callback_query(F.data == "info_techniques")
async def info_techniques(callback: CallbackQuery):
    await callback.answer()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="5-4-3-2-1", callback_data="grounding_54321")],
            [InlineKeyboardButton(text="Квадратное дыхание", callback_data="grounding_breathing")],
            [InlineKeyboardButton(text="Сканирование тела", callback_data="grounding_body_scan")]
        ]
    )
    await callback.message.answer("Выбери технику заземления:", reply_markup=keyboard)

@router.callback_query(F.data == "info_howto")
async def info_howto(callback: CallbackQuery):
    await callback.answer()
    text = "Обращаться ко мне можно:\n• @alexanderpsy_bot\n• Александр\n• Саша\n\nВ группе отвечаю только когда ко мне обращаются."
    await callback.message.answer(text)

@router.callback_query(F.data.startswith("grounding_"))
async def grounding_handler(callback: CallbackQuery):
    await callback.answer()
    technique = callback.data.split("_")[1]
    text = GROUNDING_TECHNIQUES.get(technique, "Выбери технику из списка.")
    await callback.message.answer(text)
