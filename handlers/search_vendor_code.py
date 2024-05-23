import logging
from aiogram import F, Router, types
from aiogram.filters import CommandStart, Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from kbds.reply import get_keyboard
from parser.pars_wb import PAGE_LIMIT, get_response
from parser.pars_geo import get_osm, get_xinfo
from utils.validate_vendor_code import validation_code


search_vendor_code_router = Router()

start_kbd = get_keyboard(
    'Начать поиск',
    'Начало',
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

@search_vendor_code_router.message(or_f(Command('search'), F.text.lower() == 'поиск'))
async def start_cmd(message: types.Message):
    await message.answer(
        f'😺😽😺\nЯ помогу найти позицию товоего товара в выдаче ВБ по поисковому запросу\n Приступим?', 
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
@search_vendor_code_router.message(StateFilter(None), F.text.lower() == 'начать поиск')
async def start_quiz(message: types.Message, state: FSMContext):
    await message.answer(
        'Использовать геолокацию по умолчанию (Москва)🌇\nили использовать Вашу?🗺️\nЛибо Вы можете указать любой интересующий Вас адрес✏️\n\
        Для возврата на шаг назад - отправь назад \n\
        Для отмены запроса - отмена', 
        reply_markup=position_kbd,
    )
    await state.set_state(AddSearchQuery.geo_position)


#хэндлер отмены и сброса состояния
@search_vendor_code_router.message(StateFilter('*'), Command('отмена'))
@search_vendor_code_router.message(StateFilter('*'), F.text.casefold() == 'отмена')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        return
    
    await state.clear()
    await message.answer('Действия отменены', reply_markup=start_kbd)

#хэндлер возврата на щаг назад
@search_vendor_code_router.message(StateFilter('*'), Command('назад'))
@search_vendor_code_router.message(StateFilter('*'), F.text.casefold() == 'назад')
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
@search_vendor_code_router.message(StateFilter(AddSearchQuery.geo_position), F.text == 'По умолчанию🌇')
async def get_geo_position_default(message: types.Message, state: FSMContext):
    dest = await get_xinfo()
    await state.update_data(geo_position=dest)
    await message.answer('Отправь мне артикул искомого товара', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddSearchQuery.vendor_code)

#Встаем в состояние ожидания ввода артикула, делаем запрос по геопозиции юзера    
@search_vendor_code_router.message(StateFilter(AddSearchQuery.geo_position), F.location)
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
@search_vendor_code_router.message(StateFilter(AddSearchQuery.geo_position), F.text == 'Ввести самостоятельно✏️')
async def get_address(message: types.Message):
    await message.answer('Отправь мне название города или более точный адрес', reply_markup=types.ReplyKeyboardRemove())
    

#по адресу получаем координаты и получаем значение dest для запроса на вб
@search_vendor_code_router.message(StateFilter(AddSearchQuery.geo_position), F.text)
async def get_geo_position_manually(message: types.Message, state: FSMContext):
    address = message.text
    coords = await get_osm(address)
    if coords['status']:
        dest = await get_xinfo(coords)
        await state.update_data(geo_position=dest)
        await message.answer('Отправь мне артикул искомого товара', reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(AddSearchQuery.vendor_code)
    else:
        logging.error('The address does not exist')
        await message.answer('Вы ввели не существующий адрес')


#хэндлер для отлова некоректных данных для геопозиции
@search_vendor_code_router.message(StateFilter(AddSearchQuery.geo_position))
async def get_geo_position_error(message: types.Message, state: FSMContext):
    await message.answer('Вы ввели недопустимые данные')


#ловим артикул и встаем в состояние ввода поискового запроса
@search_vendor_code_router.message(StateFilter(AddSearchQuery.vendor_code), F.text)
async def add_vendor_code(message: types.Message, state: FSMContext):
    # проверка на валидность артикула
    try:
        if validation_code(message.text) is False:
            raise ValueError
    except Exception as e:
        logging.exception(e)
        await message.answer(f"{message.from_user.first_name}, введите артикул корректно")
        return 
    
    await state.update_data(vendor_code=message.text)
    await message.answer('Отправь поисковый запрос')
    await state.set_state(AddSearchQuery.search_query)

#хэндлер для отлова некоректных данных для артикула
@search_vendor_code_router.message(StateFilter(AddSearchQuery.vendor_code))
async def add_vendor_code2(message: types.Message, state: FSMContext):
    await message.answer('Вы ввели недопустимые данные')

#хэндлер для отлова поискового запроса и выхода из состояния
@search_vendor_code_router.message(StateFilter(AddSearchQuery.search_query), F.text)
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

#хэндлер для отлова некорректных данных для поискового запроса
@search_vendor_code_router.message(StateFilter(AddSearchQuery.search_query), F.text)
async def add_search_query2(message: types.Message, state: FSMContext):
    await message.answer('Вы ввели недопустимые данные')
