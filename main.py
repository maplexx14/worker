from aiogram import Bot, Dispatcher, types
import logging
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN
from config import CHANNEL_ID
from config import BUTTON_TEXT



logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage = MemoryStorage())
question_index = 0 # переменная отвечающая за заполнение заявки

def read_questions(file_path='questions.txt'):
    with open(file_path, 'r', encoding='utf-8') as file:
        questions = [line.strip() for line in file.readlines()]
    return questions

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    global question_index
    question_index = 0
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_create_request = types.KeyboardButton('Создать заявку')
    button_conditions = types.KeyboardButton('Условия работы')
    keyboard.add(button_create_request, button_conditions)

    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=keyboard)

# Ответ на кнопку
@dp.message_handler(lambda message: message.text == 'Условия работы')
async def show_conditions(message: types.Message):
    await message.answer(BUTTON_TEXT, parse_mode=types.ParseMode.MARKDOWN)

@dp.message_handler(lambda message: message.text == 'Создать заявку')
async def create_request(message: types.Message):
    questions = read_questions()
    global question_index


    if questions:
        question_index += 1
        await message.answer(questions[0])
        await dp.storage.update_data(chat=message.chat.id, data={'current_question_index': 0})
        return question_index
@dp.message_handler(lambda message: message.text != 'Создать заявку')
async def error(message: types.Message):

    if question_index == 0:
        await message.answer('Вы ничего не выбрали. Начните заполнение анкеты по кнопке снизу! Никто не видит, что вы пишете.')
    else:
        current_question_index = (await dp.storage.get_data(chat=message.chat.id)).get('current_question_index', 0)
        user_answers = (await dp.storage.get_data(chat=message.chat.id)).get('user_answers', [])

        questions = read_questions()
        if current_question_index < len(questions):
            # Здесь ты можешь добавить логику проверки ответа пользователя
            # и обработку ошибок, если необходимо.

            # Сохраняем ответ пользователя
            user_answers.append(message.text)

            await dp.storage.update_data(chat=message.chat.id,
                                         data={'current_question_index': current_question_index + 1,
                                               'user_answers': user_answers})

            if current_question_index + 1 < len(questions):
                await message.answer(questions[current_question_index + 1])
            else:
                # Формируем одно сообщение с ответами и отправляем в телеграмм-канал
                answers_text = "\n".join([f"{i + 1}. {answer}" for i, answer in enumerate(user_answers)])

                await bot.send_message(CHANNEL_ID,
                                       f"[{message.from_user.username}](tg://user?id={message.from_user.id})|{message.from_user.id}:\n"
                                       f"{answers_text}", parse_mode='markdown')
                user_answers.clear()
                await message.answer("Спасибо за заполнение формы!")
        else:
            await message.answer("Форма уже заполнена.")

# база
if __name__ == '__main__':
    from aiogram import executor
    from aiogram.contrib.middlewares.logging import LoggingMiddleware

    dp.middleware.setup(LoggingMiddleware())
    executor.start_polling(dp, skip_updates=True)
