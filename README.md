# moodle-answers-backend
Backend for sharing answers in Moodle

# Установка
1. Клонируйте этот репозиторий.
2. Разверните MongoDB на локальной машине или используйте бесплатный кластер от [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
3. Измените параметры подключения к MongoDB в `app/__init__.py`, [строка 6](https://github.com/Ninja-Official/moodle-answers-backend/blob/d39701a0aec94dbe2b2b590b3430cbaf9b7520b0/app/__init__.py#L6).
4. Если вам нужно защищённое соединение по протоколу HTTPS, то необходимо задать ssl context в `run.py`.

# Запуск и использование
Для использования требуется Python 3.7+
1. `pip install -r requirements.txt`
2. `python run.py`
