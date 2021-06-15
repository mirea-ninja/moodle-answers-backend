from flask import Flask, json, make_response, request, jsonify, Markup
from flask_socketio import join_room, leave_room
from pymongo import ReturnDocument
from . import sockets, questions_collection, chat_collection
from .answers import AnswersDB


@sockets.on('chat')
def add_chat_message(data):
    room = data['room']
    data['message']['user'] = Markup.escape(data['message']['user'])
    data['message']['user_info'] = data['message']['user_info']
    data['message']['text'] = Markup.escape(data['message']['text'])

    if len(data['message']['text']) > 0 and len(data['message']['text']) < 800:
        chat_collection.find_one_and_update(
            {'room': room}, {'$push': {'messages': data['message']}}, {"_id": 0}, upsert=True)
        sockets.emit('add_chat_messages', [data['message']], to=room)


@sockets.on('get_chat')
def get_chat_messages(room):
    messages = chat_collection.find_one({'room': room}, {"_id": 0})
    if messages is not None:
        sockets.emit('add_chat_messages', messages['messages'], to=room)


@sockets.on('view_question')
def view_question(message):
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
        
            result = questions_collection.find_one(
                {'question': question}, {"_id": 0}
            )
            sockets.emit('update_answers', result, to=room)
        sockets.emit('update_viewers', result, to=room)


@sockets.on('add_answer')
def add_answer(data):
    result = AnswersDB.add_user_answer(
        data['question'], data['answer'], data['user_info'], data['question_type'])
    sockets.emit('update_answers', result, to=data['room'])
    

@sockets.on('add_approve')
def ans_approve(data):
    result = AnswersDB.add_user_approve(
        data['question'], data['answer'], data['user_info'], data['is_correct'])
    sockets.emit('update_answers', result, to=data['room'])


@sockets.on('join')
def on_join(room):
    join_room(room)


@sockets.on('leave')
def on_leave(room):
    leave_room(room)
