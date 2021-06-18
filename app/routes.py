from flask import Markup
from . import sio, questions_collection, chat_collection
from .answers import AnswersDB
from datetime import datetime


@sio.event
async def chat(sid, data):
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
    messages = chat_collection.find_one({'room': room}, {"_id": 0})
    if messages is not None:
        await sio.emit('add_chat_messages', messages['messages'], room=room)


@sio.event
async def view_question(sid, message):
    json_data = message['data']
    questions = json_data['questions']
    if len(questions) > 0:
        user_info = json_data['user_info']
        room = json_data['room']

        result = {'data': []}
        for question in questions:
            question.replace('Вы можете помочь развитию проекта, подтвердив правильный ответ (нужно нажать  на правильный ответ)Впишите суда свой ответ, если его нет внизу. Затем нажмите на пустое место рядом с полем и ответ сохранится. Пожалуйста, опишите ответ словами, не вставляйте буквы или номера ответов, они каждый раз меняются.', '')
            data = AnswersDB.add_new_viewer(question, user_info)
            result['data'].append(data)

            result_question = questions_collection.find_one(
                {'question': question}, {"_id": 0}
            )
            await sio.emit('update_answers', result_question, room=room)
        await sio.emit('update_viewers', result, room=room)


@sio.event
async def add_answer(sid, data):
    result = AnswersDB.add_user_answer(
        data['question'], data['answer'], data['user_info'], data['question_type'])
    await sio.emit('update_answers', result, room=data['room'])


@sio.event
async def add_approve(sid, data):
    if isinstance(data['answer'], list):
        if len(data['answer']) == 2:
            data['answer'] = 0
    result = AnswersDB.add_user_approve(
        data['question'], data['answer'], data['user_info'], data['is_correct'])
    await sio.emit('update_answers', result, room=data['room'])


@sio.event
async def join(sid, room):
    sio.enter_room(sid, room)


@sio.event
async def leave(sid, room):
    sio.leave_room(sid, room)
