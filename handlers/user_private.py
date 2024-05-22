import logging
from aiogram import F, Router, types
from aiogram.filters import CommandStart, Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from kbds.reply import get_keyboard
from parser.pars_wb import PAGE_LIMIT, get_response
from parser.pars_geo import get_osm, get_xinfo

user_private_router = Router()

start_kbd = get_keyboard(
    'Поиск',
    placeholder='выберите действие',
    sizes=(1,),
)

position_kbd = get_keyboard(
    'По умолчанию🌇',
    'Передать🗺️',
    'Ввести самостоятельно✏️',
    placeholder='передайте координаты',
    request_location=1,
    sizes=(2, 1,),
)

@user_private_router.message(or_f(CommandStart(), F.text.lower() == 'start'))
async def start_cmd(message: types.Message):
    await message.answer(
        f'Привет😺😽😺\nя помогу найти позицию товоего товара в выдаче ВБ по поисковому запросу\n ', 
        reply_markup=start_kbd,
    )    

#################FSM####################
    
class AddSearchQuery(StatesGroup):
    geo_position = State()
    vendor_code = State()
    search_query = State()

    texts = {
        'AddSearchQuery:geo_position': 'Отправьте Вашу локацию заново',
        'AddSearchQuery:vendor_code': 'Введите артикул заново',
        'AddSearchQuery:search_query': 'Введите поисковый запрос заново',
    }


#Опрашиваем пользователя о необходимости использовать его геолокацию при дальнейшим парсинге, встаем в состояние ожидания ввода геоданных
@user_private_router.message(StateFilter(None), F.text.lower() == 'поиск')
async def start_quiz(message: types.Message, state: FSMContext):
    await message.answer(
        f'Использовать геолокацию по умолчанию (Москва)🌇\n или использовать Вашу?🗺️\nЛибо Вы можете указать любой интересующий Вас адрес✏️', 
        reply_markup=position_kbd,
    )
    await state.set_state(AddSearchQuery.geo_position)


#хэндлер отмены и сброса состояния
@user_private_router.message(StateFilter('*'), Command('отмена'))
@user_private_router.message(StateFilter('*'), F.text.casefold() == 'отмена')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        return
    
    await state.clear()
    await message.answer('Действия отменены', reply_markup=start_kbd)

#хэндлер возврата на щаг назад
@user_private_router.message(StateFilter('*'), Command('назад'))
@user_private_router.message(StateFilter('*'), F.text.casefold() == 'назад')
async def back_step_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state == AddSearchQuery.geo_position:
        await message.answer('Предыдущего шага нет, введите артикул или отмена')
        return
    
    previous = None
    for step in AddSearchQuery.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f'Ок вы вернулись к предыдущему шагу \n {AddSearchQuery.texts[previous.state]}')
            return
        previous = step


#Встаем в состояние ожидания ввода артикула, делаем запрос по геопозиции по умолчанию  
@user_private_router.message(StateFilter(AddSearchQuery.geo_position), F.text == 'По умолчанию🌇')
async def get_geo_position_default(message: types.Message, state: FSMContext):
    dest = await get_xinfo()
    await state.update_data(geo_position=dest)
    await message.answer('Отправь мне артикул искомого товара', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddSearchQuery.vendor_code)

#Встаем в состояние ожидания ввода артикула, делаем запрос по геопозиции юзера    
@user_private_router.message(StateFilter(AddSearchQuery.geo_position), F.location)
async def get_geo_position_user(message: types.Message, state: FSMContext):
    
    geo_data = {
        'longitude': message.location.longitude,
        'latitude': message.location.latitude,
    }
    
    dest = await get_xinfo(geo_data)

    await state.update_data(geo_position=dest)
    await message.answer('Отправь мне артикул искомого товара', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddSearchQuery.vendor_code)


#предлагаем ввести адресс
@user_private_router.message(StateFilter(AddSearchQuery.geo_position), F.text == 'Ввести самостоятельно✏️')
async def get_address(message: types.Message):
    await message.answer('Отправь мне название города или более точный адрес', reply_markup=types.ReplyKeyboardRemove())
    

#по адресу получаем координаты и получаем значение dest для запроса на вб
@user_private_router.message(StateFilter(AddSearchQuery.geo_position), F.text)
async def get_geo_position_manually(message: types.Message, state: FSMContext):
    address = message.text
    coords = await get_osm(address)
    if coords['status']:
        dest = await get_xinfo(coords)
        await state.update_data(geo_position=dest)
        await message.answer('Отправь мне артикул искомого товара', reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AddSearchQuery.vendor_code)
    else:
        await message.answer('Вы ввели недопустимые данные')


#хэндлер для отлова некоректных данных для геопозиции
@user_private_router.message(StateFilter(AddSearchQuery.geo_position))
async def get_geo_position_error(message: types.Message, state: FSMContext):
    await message.answer('Вы ввели недопустимые данные')


#ловим артикул и встаем в состояние ввода поискового запроса
@user_private_router.message(StateFilter(AddSearchQuery.vendor_code), F.text)
async def add_vendor_code(message: types.Message, state: FSMContext):
    # проверка на валидность артикула
    try:
        int(message.text)
    except ValueError:
        await message.answer("Введите артикул корректно")
        return
    try:
        len(message.text) // 7 
    
    await state.update_data(vendor_code=message.text)
    await message.answer('Отправь поисковый запрос')
    await state.set_state(AddSearchQuery.search_query)

#хэндлер для отлова некоректных данных для артикула
@user_private_router.message(StateFilter(AddSearchQuery.vendor_code))
async def add_vendor_code2(message: types.Message, state: FSMContext):
    await message.answer('Вы ввели недопустимые данные')

#хэндлер для отлова поискового запроса и выхода из состояния
@user_private_router.message(StateFilter(AddSearchQuery.search_query), F.text)
async def add_search_query(message: types.Message, state: FSMContext):
    await state.update_data(search_query=message.text)
    await message.answer('Запрос получен, ожидайте...', reply_markup=types.ReplyKeyboardRemove())
    data = await state.get_data()
    # try:
    response = await get_response(data)

    if response['status']:   
        await message.answer(
            f"Товар арт.{data['vendor_code']} по запросу '{data['search_query']}' находится на {str(response['page'])} странице на {str(response['place'])} месте.", 
            reply_markup=start_kbd
        )
    else:
        await message.answer(
            f"Товар арт.{data['vendor_code']} по запросу '{data['search_query']}' не найден на первых {PAGE_LIMIT} страницах", 
            reply_markup=start_kbd
        )
        
    await state.clear()

    # except Exception as e:
    #     logging.exception(e)
    #     await message.answer(
    #             f"Товар арт.{data['vendor_code']} по запросу '{data['search_query']}' не найден. Проверьте, может быть вы ввели что-то не так?", 
    #             reply_markup=start_kbd
    #         )
    #     await state.clear()

#хэндлер для отлова некорректных данных для поискового запроса
@user_private_router.message(StateFilter(AddSearchQuery.search_query), F.text)
async def add_search_query2(message: types.Message, state: FSMContext):
    await message.answer('Вы ввели недопустимые данные')








@user_private_router.message(Command('about'))
async def about_cmd(message: types.Message):
    await message.answer('Функционал находится в разработке')


@user_private_router.message(Command('payment'))
async def payment_cmd(message: types.Message):
    await message.answer('Функционал находится в разработке')


@user_private_router.message(or_f(Command('menu'), F.text.lower() == 'меню'))
async def menu_cmd(message: types.Message):
    await message.answer('Функционал находится в разработке')
