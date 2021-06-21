from flask import Markup
from . import sio, questions_collection, chat_collection
from .answers import AnswersDB
from datetime import datetime


@sio.event
async def chat(sid, data):
    """Отправка сообщения в чат

    Args:
        * sid (str): Socket.IO session id
        * data (dict): словарь, в котором ключи: 
            * room (str) - идентификатор вопроса для комнаты (хэш текста первого вопроса на странице),
            * message (dict): ключи:
                * user (str) - имя пользователя,
                * user_info (str) - уникальный visitorId пользователя,
                * text (str) - текст сообщения
    """
    room = data['room']
    data['message']['user'] = Markup.escape(data['message']['user'])
    data['message']['user_info'] = data['message']['user_info']
    data['message']['text'] = Markup.escape(data['message']['text'])

    if len(data['message']['text']) > 0 and len(data['message']['text']) < 800:
        chat_collection.find_one_and_update(
            {'room': room}, {'$push': {'messages': data['message']}}, {"_id": 0}, upsert=True)
        await sio.emit('add_chat_messages', [data['message']], room=room)


@sio.event
async def get_chat(sid, room):
    """Отправляет клиенту историю чата для конкретной комнаты

    Args:
        sid (str): Socket.IO session id
        room (str) - идентификатор вопроса для комнаты (хэш текста первого вопроса на странице)
    """
    messages = chat_collection.find_one({'room': room}, {"_id": 0})
    if messages is not None:
        await sio.emit('add_chat_messages', messages['messages'], room=room)


@sio.event
async def view_question(sid, message):
    """Добавляет просмотр пользователя на вопросы или создаёт вопросы, 
    если таких ещё не было

    Args:
        * sid (str): Socket.IO session id
        * message (dict): данные о вопросе, ключи:
            * questions (list of str): список текстов вопросов на странице 
            * data (dict): информация о пользователе. Ключи:
                * user_info (str) - уникальный visitorId пользователя,
                * room (str) - идентификатор вопроса для комнаты (хэш текста первого 
                вопроса на странице)
        
        Пример message:
        {
            'questions': ['Вопрос 1', 'Вопрос 2', 'Вопрос 3'],
            'data': {'user_info': 'a177af1c0fcce3f25c2290ffde69716c', 'room': 'a177af1c0fcce3f25c2290ffde69716c'}
        }
        
        Пример message:
        {
            'questions': ['Один вопрос на странице'],
            'data': {'user_info': 'a177af1c0fcce3f25c2290ffde69716c', 'room': 'a177af1c0fcce3f25c2290ffde69716c'}
        }
    """
    json_data = message['data']
    questions = json_data['questions']
    if len(questions) > 0:
        user_info = json_data['user_info']
        room = json_data['room']

        result = {'data': []}
        for question in questions:
            question = question.replace('Вы можете помочь развитию проекта, подтвердив правильный ответ (нужно нажать  на правильный ответ)Впишите суда свой ответ, если его нет внизу. Затем нажмите на пустое место рядом с полем и ответ сохранится. Пожалуйста, опишите ответ словами, не вставляйте буквы или номера ответов, они каждый раз меняются.', '')
            data = AnswersDB.add_new_viewer(question, user_info)
            result['data'].append(data)

            result_question = questions_collection.find_one(
                {'question': question}, {"_id": 0}
            )
            await sio.emit('update_answers', result_question, room=room)
        await sio.emit('update_viewers', result, room=room)


@sio.event
async def add_answer(sid, data):
    """Добавляет ответ пользователя на вопрос

    Args:
        * sid (str): Socket.IO session id
        * data (dict): словарь, в котором ключи: 
            * question (str) - текст вопроса,
            * answer (str/dict) - информация о выбранном ответе. Если строка - текст ответа, если список, 
            то 1-й элемент - текст ответа, второй элемент - состояние (checked),  
            * user_info (str) - уникальный visitorId пользователя, 
            * question_type (str) - типы вопросов: 'shortanswer', 'truefalse', 'numerical', 'multichoice',
            'multichoice_checkbox', 'match' (пока не поддерживается)
            * room (str) - идентификатор вопроса для комнаты (хэш текста первого вопроса на странице)
        
        Пример data:
        {
            'question': 'Правильно или неправильно?', 'answer': ['Правильно', True], 
            'user_info': 'a177af1c0fcce3f25c2290ffde69716c', 
            'question_type': 'multichoice_checkbox', 'room': 'a177af1c0fcce3f25c2290ffde69716c'
        }
        
    """
    result = AnswersDB.add_user_answer(
        data['question'], data['answer'], data['user_info'], data['question_type'])
    if result is not None:
        await sio.emit('update_answers', result, room=data['room'])


@sio.event
async def add_approve(sid, data):
    """Добавляет подтверждение ппользователя в поля "уверен, что правильно"
    или "уверен, что неправильно"

    Args:
        * sid (str): Socket.IO session id
        * data (dict): словарь, в котором ключи: 
            * question (str) - текст вопроса,
            * answer (str/dict) - информация о выбранном ответе. Если строка - 
            текст ответа, если список, то 1-й элемент - текст ответа, второй 
            элемент - состояние (checked), 
            * user_info (str) - уникальный visitorId пользователя, 
            * is_correct (bool) - True - пользователь уверен, что это правильно, 
            False - пользователь уверен, что это неправильно
            * room (str) - идентификатор вопроса для комнаты (хэш текста первого вопроса на странице)
        
        Пример data: 
        {
            'question': 'Правильно или неправильно?', 'answer': ['Правильно', True], 
            'user_info': 'a177af1c0fcce3f25c2290ffde69716c', 
            'is_correct': False, 'room': 'a177af1c0fcce3f25c2290ffde69716c'
        }
        
        Пример data: 
        {
            'question': 'Какой тут ответ?', 'answer': '13', 
            'user_info': 'a177af1c0fcce3f25c2290ffde69716c', 
            'is_correct': True, 'room': 'a177af1c0fcce3f25c2290ffde69716c'
        }
        
    """
    # у checkbox-подобных типов отправляется ещё и состояние
    # выбора этого ответа (checked), поэтому берём только
    # сам текст ответа
    if isinstance(data['answer'], list):
        if len(data['answer']) == 2:
            data['answer'] = 0
            
    result = AnswersDB.add_user_approve(
        data['question'], data['answer'], data['user_info'], data['is_correct'])
    if result is not None:
        await sio.emit('update_answers', result, room=data['room'])


@sio.event
async def join(sid, room):
    """Вход в комнату вопроса. Вызывается при загрузке страницы 
    вопроса

    Args:
        sid (str): Socket.IO session id
        room (str): идентификатор вопроса для комнаты (хэш текста первого вопроса на странице)
    """
    sio.enter_room(sid, room)


@sio.event
async def leave(sid, room):
    """Выход из комнаты вопроса

    Args:
        sid (str): Socket.IO session id
        room (str): идентификатор вопроса для комнаты (хэш текста первого вопроса на странице)
    """
    sio.leave_room(sid, room)
