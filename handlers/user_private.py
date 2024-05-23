from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart, or_f

from kbds.reply import get_keyboard
from handlers.search_vendor_code import search_vendor_code_router


user_private_router = Router()
user_private_router.include_router(search_vendor_code_router)

start_kbd = get_keyboard(
    'Поиск',
    'Остаток товара',
    placeholder='выберите действие',
    sizes=(1,1,),
)


@user_private_router.message(CommandStart(), F.text.lower() == 'начало')
async def start_cmd(message: types.Message):
    await message.answer(f'Привет, {message.from_user.first_name}, я бот Pomogator, я помогу тебя)))', reply_markup=start_kbd)


@user_private_router.message(Command('about'))
async def about_cmd(message: types.Message):
    await message.answer('Функционал находится в разработке')


@user_private_router.message(Command('payment'))
async def payment_cmd(message: types.Message):
    await message.answer('Функционал находится в разработке')


@user_private_router.message(or_f(Command('menu'), F.text.lower() == 'меню'))
async def menu_cmd(message: types.Message):
    await message.answer('Функционал находится в разработке')