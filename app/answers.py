from pymongo import ReturnDocument
from . import client, questions_collection

class AnswersDB:
    @staticmethod
    def find_question(question, session):
        result = questions_collection.find_one(
            {'question': question}, {"_id": 0},
            session=session
        )
        return result

    @staticmethod
    def find_question_by_ans(question, answer, session):
        # для типа вопроса 'match'
        if 'subquestion' in answer:
            result = questions_collection.find_one(
                {'question': question, 
                 'answers.subquestion': answer['subquestion'], 
                 'answers.answer': answer['answer']
                 }, {"_id": 0},
                session=session
            )
        else:
            result = questions_collection.find_one(
                {'question': question, 'answers.answer': answer}, {"_id": 0},
                session=session
            )
        return result

    @staticmethod
    def add_new_question(question, answers, viewers, session):
        """Добавляет вопрос

        Args:
            question (str): текст вопроса
            answers (list): список ответов
            viewers (list): список пользователей, которые просмотрели вопрос
        """
        insert_data = {'question': question,
                       'answers': answers, 'viewers': viewers}
        questions_collection.insert_one(insert_data, session=session)

    @staticmethod
    def add_user_answer(question, answer, user_info, question_type):
        """Добавляет вариант ответа пользователя в впорос

        Args:
            question (str): текст вопроса
            answer (str): выбранный вариант ответа
            user_info (str): секретный хэш пользователя
            question_type (str): тип вопроса

        Returns:
            [type]: [description]
        """
        
        with client.start_session(causal_consistency=True) as session:
            # вариант вопроса с одним возможным ответом
            if question_type == 'shortanswer' or question_type == 'numerical' or question_type == 'multichoice' or question_type == 'truefalse':
                # удаляем другие наши ответы и добавляем новый
                questions_collection.update_many(
                    {'question': question, 'answers.users': user_info},
                    {'$pull': {'answers.$.users': user_info}}, 
                    session=session
                )
                
                if question_type == 'shortanswer' or question_type == 'numerical':
                    AnswersDB.delete_empty_answers(question, session)

                if AnswersDB.find_question_by_ans(question, answer, session) is None:
                    return questions_collection.find_one_and_update(
                        {'question': question}, {'$push': {'answers': {'answer': answer, 'users': [user_info], 'correct': [], 'not_correct': []}}},
                        {"_id": 0}, return_document=ReturnDocument.AFTER, session=session)
                else:
                    return questions_collection.find_one_and_update(
                        {'question': question, 'answers.answer': answer},
                        {'$push': {'answers.$.users': user_info}}, {"_id": 0},
                        return_document=ReturnDocument.AFTER, session=session)
                    
            elif question_type == 'multichoice_checkbox':
                result = None
                if answer[1] is False:
                    result = questions_collection.find_one_and_update(
                        {'question': question, 'answers.answer': answer[0]},
                        {'$pull': {'answers.$.users': user_info}}, {"_id": 0},
                        return_document=ReturnDocument.AFTER, session=session
                    )
                else:
                    # если пользователь не отпралял этот вариант ответа
                    if AnswersDB.is_user_send_answer(question, answer[0], user_info, session) is False:
                        if AnswersDB.find_question_by_ans(question, answer[0], session) is None:
                            result = questions_collection.find_one_and_update(
                                {'question': question}, 
                                {'$push': {'answers': {'answer': answer[0], 'users': [user_info], 'correct': [], 'not_correct': []}}}, 
                                {"_id": 0}, return_document=ReturnDocument.AFTER, session=session
                            )
                        else:
                            result = questions_collection.find_one_and_update(
                                {'question': question, 'answers.answer': answer[0]},
                                {'$push': {'answers.$.users': user_info}}, {"_id": 0},
                                return_document=ReturnDocument.AFTER, session=session
                            )
                    
                if result is None:
                    return AnswersDB.find_question(question, session)
                return result
            
            elif question_type == 'match':
                subquestion = answer[0]
                answer_text = answer[1]
                
                 # если пользователь точно такой ответ не отправлял
                if not AnswersDB.is_user_send_answer(question, answer, user_info, session):
                    # удаляем другие ответы пользователя на такой subquestion
                    questions_collection.update_many(
                        {'question': question, 'answers.users': user_info, 'answers.subquestion': subquestion},
                        {'$pull': {'answers.$.users': user_info}}, 
                        session=session
                    )
                    AnswersDB.delete_empty_answers(question, session)
                    match_answer = {'subquestion': subquestion, 'answer': answer_text}
                    if AnswersDB.find_question_by_ans(question, match_answer, session) is None:
                        return questions_collection.find_one_and_update(
                            {'question': question}, {'$push': {'answers': {'subquestion': subquestion, 'answer': answer_text, 'users': [user_info], 'correct': [], 'not_correct': []}}},
                            {"_id": 0}, return_document=ReturnDocument.AFTER, session=session)
                    else:
                        return questions_collection.find_one_and_update(
                            {'question': question, 'answers.subquestion': subquestion, 'answers.answer': answer_text},
                            {'$push': {'answers.$.users': user_info}}, {"_id": 0},
                            return_document=ReturnDocument.AFTER, session=session)
                    

    @staticmethod
    def add_user_approve(question, answer, user_info, is_correct):
        with client.start_session(causal_consistency=True) as session:
            questions_collection.update_one(
                {'question': question, 'answers.answer': answer},
                {'$pull': {'answers.$.correct': user_info}}, 
                session=session
            )
            questions_collection.update_one(
                {'question': question, 'answers.answer': answer},
                {'$pull': {'answers.$.not_correct': user_info}}, 
                session=session
            )

            if is_correct:
                if AnswersDB.find_question_by_ans(question, answer, session) is None:
                    return questions_collection.find_one_and_update(
                        {'question': question},
                        {'$push': {'answers': {'answer': answer, 'users': [], 'correct': [user_info], 'not_correct': []}}}, {"_id": 0},
                        return_document=ReturnDocument.AFTER, session=session
                    )
                else:
                    return questions_collection.find_one_and_update(
                        {'question': question, 'answers.answer': answer},
                        {'$push': {'answers.$.correct': user_info}}, {"_id": 0},
                        return_document=ReturnDocument.AFTER, session=session
                    )
            else:
                if AnswersDB.find_question_by_ans(question, answer, session) is None:
                    return questions_collection.find_one_and_update(
                        {'question': question},
                        {'$push': {'answers': {'answer': answer, 'users': [], 'correct': [], 'not_correct': [user_info]}}}, {"_id": 0},
                        return_document=ReturnDocument.AFTER, session=session
                    )
                else:
                    return questions_collection.find_one_and_update(
                        {'question': question, 'answers.answer': answer},
                        {'$push': {'answers.$.not_correct': user_info}}, {"_id": 0},
                        return_document=ReturnDocument.AFTER, session=session
                    )

                
    @staticmethod
    def add_new_viewer(question, user_info):
        """Добавляет новый просмотр в вопрос или создаёт вопрос с просмотром,
        если такого вопроса ещё нет

        Args:
            question (str): текст вопроса
            user_info (str): секретный хэш пользователя

        Returns:
            dict: возвращает обхект вопроса
        """
        with client.start_session(causal_consistency=True) as session:
            question_db = AnswersDB.find_question(question, session)
            if question_db is not None:
                if user_info not in question_db['viewers']:
                    document = questions_collection.find_one_and_update(
                        {'question': question}, {'$push': {'viewers': user_info}},
                        {"_id": 0}, return_document=ReturnDocument.AFTER, session=session
                    )
                    return document
                else:
                    return question_db
            else:
                AnswersDB.add_new_question(question, [], [user_info], session)
                return {'question': question, 'answers': [], 'viewers': [user_info]}

    @staticmethod
    def is_user_send_answer(question, answer, user_info, session):
        question = questions_collection.find_one(
            {'question': question},
            session=session
        )
        
        for answer_ in question['answers']:
            # для типа вопроса 'match'
            if 'subquestion' in answer_:
                if answer_['subquestion'] == answer[0] and answer_['answer'] == answer[1]:
                    if user_info in answer_['users']:
                        return True
            else:
                if answer_['answer'] == answer:
                    for user in answer_['users']:
                        if user == user_info:
                            return True

        return False

    @staticmethod
    def delete_empty_answers(question, session):
        questions_collection.update_many(
            {'question': question, 'answers.users': {'$size': 0}},
            {'$set': {'answers.$': None}},
            session=session
        )
        questions_collection.update_many(
            {'question': question},
            {'$pull': {'answers': None}},
            session=session
        )

    @staticmethod
    def is_user_send_any_answer(question, user_info, session):
        find = questions_collection.find_one(
            {'question': question, "answers.users": user_info},
            session=session
        )

        if find is not None:
            return True
        return False
