from pymongo import ReturnDocument
from . import questions_collection


class AnswersDB:
    @staticmethod
    def find_question(question):
        result = questions_collection.find_one(
            {'question': question}, {"_id": 0})
        return result

    @staticmethod
    def find_question_by_ans(question, answer):
        result = questions_collection.find_one(
            {'question': question, 'answers.answer': answer}, {"_id": 0})
        return result

    @staticmethod
    def add_new_question(question, answers, viewers):
        """Добавляет вопрос

        Args:
            question (str): текст вопроса
            answers (list): список ответов
            viewers (list): список пользователей, которые просмотрели вопрос
        """
        insert_data = {'question': question,
                       'answers': answers, 'viewers': viewers}
        questions_collection.insert_one(insert_data)

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
        # вариант вопроса с одним возможным ответом
        if question_type == 'shortanswer' or question_type == 'multichoice' or question_type == 'truefalse':
            # удаляем другие наши ответы и добавляем новый
            questions_collection.update_one(
                {'question': question, 'answers.users': user_info},
                {'$pull': {'answers.$.users': user_info}}
            )
    
            questions_collection.update(
                {'question': question, 'answers.users': {'$size': 0}},
                {'$set': {'answers.$': None}}
            )
            questions_collection.update(
                {'question': question},
                {'$pull': {'answers': None}}
            )

            if AnswersDB.find_question_by_ans(question, answer) is None:
                result = questions_collection.find_one_and_update(
                    {'question': question},
                    {'$push': {'answers': {'answer': answer, 'users': [user_info]}}}, 
                    {"_id": 0},
                    return_document=ReturnDocument.AFTER
                )
                return result
            else:
                result = questions_collection.find_one_and_update(
                    {'question': question, 'answers.answer': answer},
                    {'$push': {'answers.$.users': user_info}}, {"_id": 0},
                    return_document=ReturnDocument.AFTER)
                return result

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
        question_db = AnswersDB.find_question(question)
        if question_db is not None:
            if user_info not in question_db['viewers']:
                document = questions_collection.find_one_and_update(
                    {'question': question}, {'$push': {'viewers': user_info}},
                    {"_id": 0}, return_document=ReturnDocument.AFTER
                )
                return document
            else:
                return question_db
        else:
            AnswersDB.add_new_question(question, [], [user_info])
            return {'question': question, 'answers': [], 'viewers': [user_info]}

    @staticmethod
    def is_user_send_answer(question, answer, user_info):
        find = questions_collection.find_one(
            {'question': question, "answers.ans": answer, "answers.users": user_info})

        if find is not None:
            return True
        return False

    @staticmethod
    def is_user_send_any_answer(question, user_info):
        find = questions_collection.find_one(
            {'question': question, "answers.users": user_info})

        if find is not None:
            return True
        return False
