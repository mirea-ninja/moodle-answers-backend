from re import sub
from pymongo import ReturnDocument

from app.config import DATABASE_NAME, QUESTIONS_COLLECTION_NAME


class AnswersDB:
    @staticmethod
    async def find_question(conn, question, session):
        result = await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one(
            {'question': question}, {"_id": 0},
            session=session
        )
        return result

    @staticmethod
    async def find_question_by_ans(conn, question, answer, session):
        # для типа вопроса 'match'
        if 'subquestion' in answer:
            result = await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one(
                {'question': question,
                 'answers.subquestion': answer['subquestion']
                 }, {"_id": 0},
                session=session
            )

            if result is not None:
                for answer_ in result['answers']:
                    if answer_['subquestion'] == answer['subquestion'] and answer_['answer'] == answer['answer']:
                        return result
                result = None
        else:
            result = await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one(
                {'question': question, 'answers.answer': answer}, {"_id": 0},
                session=session
            )
        return result

    @staticmethod
    async def add_new_question(conn, question, answers, viewers, session):
        """Добавляет вопрос

        Args:
            question (str): текст вопроса
            answers (list): список ответов
            viewers (list): список пользователей, которые просмотрели вопрос
        """
        insert_data = {'question': question,
                       'answers': answers, 'viewers': viewers}
        await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].insert_one(
            insert_data, session=session)

    @staticmethod
    async def add_user_answer(conn, question, answer, user_info, question_type):
        """Добавляет вариант ответа пользователя в впорос

        Args:
            question (str): текст вопроса
            answer (str): выбранный вариант ответа
            user_info (str): секретный хэш пользователя
            question_type (str): тип вопроса

        Returns:
            [type]: [description]
        """

        async with await conn.start_session(causal_consistency=True) as session:
            # вариант вопроса с одним возможным ответом
            if question_type in [
                'shortanswer',
                'numerical',
                'multichoice',
                'truefalse',
            ]:
                # удаляем другие наши ответы и добавляем новый
                await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].update_many(
                    {'question': question, 'answers.users': user_info},
                    {'$pull': {'answers.$.users': user_info}},
                    session=session
                )

                if question_type in ['shortanswer', 'numerical']:
                    await AnswersDB.delete_empty_answers(conn, question, session)

                if await AnswersDB.find_question_by_ans(conn, question, answer, session) is None:
                    return await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one_and_update(
                        {'question': question}, {'$push': {'answers': {
                            'answer': answer, 'users': [user_info], 'correct': [], 'not_correct': []}}},
                        {"_id": 0}, return_document=ReturnDocument.AFTER, session=session)
                else:
                    return await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one_and_update(
                        {'question': question, 'answers.answer': answer},
                        {'$push': {'answers.$.users': user_info}}, {"_id": 0},
                        return_document=ReturnDocument.AFTER, session=session)

            elif question_type == 'multichoice_checkbox':
                result = None
                if answer[1] is False:
                    result = await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one_and_update(
                        {'question': question, 'answers.answer': answer[0]},
                        {'$pull': {'answers.$.users': user_info}}, {"_id": 0},
                        return_document=ReturnDocument.AFTER, session=session
                    )
                elif await AnswersDB.is_user_send_answer(conn, question, answer[0], user_info, session) is False:
                    result = (
                        await conn[DATABASE_NAME][
                            QUESTIONS_COLLECTION_NAME
                        ].find_one_and_update(
                            {'question': question},
                            {
                                '$push': {
                                    'answers': {
                                        'answer': answer[0],
                                        'users': [user_info],
                                        'correct': [],
                                        'not_correct': [],
                                    }
                                }
                            },
                            {"_id": 0},
                            return_document=ReturnDocument.AFTER,
                            session=session,
                        )
                        if await AnswersDB.find_question_by_ans(
                            conn, question, answer[0], session
                        )
                        is None
                        else await conn[DATABASE_NAME][
                            QUESTIONS_COLLECTION_NAME
                        ].find_one_and_update(
                            {'question': question, 'answers.answer': answer[0]},
                            {'$push': {'answers.$.users': user_info}},
                            {"_id": 0},
                            return_document=ReturnDocument.AFTER,
                            session=session,
                        )
                    )

                if result is None:
                    return await AnswersDB.find_question(conn, question, session)
                return result

            elif question_type == 'match':
                    subquestion = answer[0]
                    answer_text = answer[1]
                    if answer_text != 'none' and answer_text is not None:
                        # если пользователь точно такой ответ не отправлял
                        if not await AnswersDB.is_user_send_answer(conn, question, answer, user_info, session):
                            # удаляем другие ответы пользователя на такой subquestion
                            await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].update_many(
                                {'question': question, 'answers.subquestion': subquestion},
                                {'$pull': {'answers.$[e].users': user_info}},
                                array_filters=[
                                    {"e.subquestion": {'$eq': subquestion}}],
                                upsert=False,
                                session=session
                            )
                            await AnswersDB.delete_empty_answers(conn, question, session)
                            match_answer = {
                                'subquestion': subquestion, 'answer': answer_text}
                            if await AnswersDB.find_question_by_ans(conn, question, match_answer, session) is None:
                                return await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one_and_update(
                                    {'question': question}, {'$push': {'answers': {'subquestion': subquestion,
                                                                                'answer': answer_text, 'users': [user_info], 'correct': [], 'not_correct': []}}},
                                    {"_id": 0}, return_document=ReturnDocument.AFTER, session=session)
                            else:
                                return await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one_and_update(
                                    {'question': question,
                                        'answers.subquestion': subquestion},
                                    {'$push': {'answers.$[e].users': user_info}},
                                    {"_id": 0},
                                    array_filters=[
                                        {"e.subquestion": {'$eq': subquestion}, "e.answer": {'$eq': answer_text}}],
                                    return_document=ReturnDocument.AFTER, session=session)
                    else:
                        # если значение у ответа = none, то пользователь снял свой выбор.
                        conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].update_many(
                            {'question': question, 'answers.subquestion': subquestion},
                            {'$pull': {'answers.$.users': user_info}},
                            session=session
                        )
                        await AnswersDB.delete_empty_answers(conn, question, session)
                        return await AnswersDB.find_question(conn, question, session)

    @staticmethod
    async def add_user_approve(conn, question, answer, user_info, is_correct):
        async with await conn.start_session(causal_consistency=True) as session:
            await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].update_one(
                {'question': question, 'answers.answer': answer},
                {'$pull': {'answers.$.correct': user_info}},
                session=session
            )
            await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].update_one(
                {'question': question, 'answers.answer': answer},
                {'$pull': {'answers.$.not_correct': user_info}},
                session=session
            )

            if is_correct:
                return (
                    await conn[DATABASE_NAME][
                        QUESTIONS_COLLECTION_NAME
                    ].find_one_and_update(
                        {'question': question},
                        {
                            '$push': {
                                'answers': {
                                    'answer': answer,
                                    'users': [],
                                    'correct': [user_info],
                                    'not_correct': [],
                                }
                            }
                        },
                        {"_id": 0},
                        return_document=ReturnDocument.AFTER,
                        session=session,
                    )
                    if await AnswersDB.find_question_by_ans(
                        conn, question, answer, session
                    )
                    is None
                    else await conn[DATABASE_NAME][
                        QUESTIONS_COLLECTION_NAME
                    ].find_one_and_update(
                        {'question': question, 'answers.answer': answer},
                        {'$push': {'answers.$.correct': user_info}},
                        {"_id": 0},
                        return_document=ReturnDocument.AFTER,
                        session=session,
                    )
                )

            if await AnswersDB.find_question_by_ans(conn, question, answer, session) is None:
                return await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one_and_update(
                    {'question': question},
                    {'$push': {'answers': {'answer': answer, 'users': [],
                                           'correct': [], 'not_correct': [user_info]}}}, {"_id": 0},
                    return_document=ReturnDocument.AFTER, session=session
                )
            else:
                return await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one_and_update(
                    {'question': question, 'answers.answer': answer},
                    {'$push': {'answers.$.not_correct': user_info}}, {"_id": 0},
                    return_document=ReturnDocument.AFTER, session=session
                )

    @staticmethod
    async def add_new_viewer(conn, question, user_info):
        """Добавляет новый просмотр в вопрос или создаёт вопрос с просмотром,
        если такого вопроса ещё нет

        Args:
            question (str): текст вопроса
            user_info (str): секретный хэш пользователя

        Returns:
            dict: возвращает обхект вопроса
        """
        async with await conn.start_session(causal_consistency=True) as session:
            question_db = await AnswersDB.find_question(conn, question, session)
            if question_db is not None:
                if user_info in question_db['viewers']:
                    return question_db
                document = await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one_and_update(
                    {'question': question}, {
                        '$push': {'viewers': user_info}},
                    {"_id": 0}, return_document=ReturnDocument.AFTER, session=session
                )
                return document
            else:
                await AnswersDB.add_new_question(conn, question, [], [user_info], session)
                return {'question': question, 'answers': [], 'viewers': [user_info]}

    @staticmethod
    async def is_user_send_answer(conn, question, answer, user_info, session):
        question = await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one(
            {'question': question},
            session=session
        )
        if question is not None:
            for answer_ in question['answers']:
                # для типа вопроса 'match'
                if 'subquestion' in answer_:
                    if (
                        answer_['subquestion'] == answer[0]
                        and answer_['answer'] == answer[1]
                        and user_info in answer_['users']
                    ):
                        return True
                elif answer_['answer'] == answer:
                    for user in answer_['users']:
                        if user == user_info:
                            return True

        return False

    @staticmethod
    async def delete_empty_answers(conn, question, session):
        await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].update_many(
            {'question': question, 'answers.users': {'$size': 0}},
            {'$set': {'answers.$': None}},
            session=session
        )
        await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].update_many(
            {'question': question},
            {'$pull': {'answers': None}},
            session=session
        )

    @staticmethod
    async def is_user_send_any_answer(conn, question, user_info, session):
        find = await conn[DATABASE_NAME][QUESTIONS_COLLECTION_NAME].find_one(
            {'question': question, "answers.users": user_info},
            session=session
        )

        return find is not None
