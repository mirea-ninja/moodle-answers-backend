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
            {'question': question, 'answers.ans': answer}, {"_id": 0})
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
                document = questions_collection.find_one_and_update({'question': question},
                                                                    {'$push': {'viewers': user_info}}, 
                                                                    {"_id": 0},
                                                                    return_document=ReturnDocument.AFTER)
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
