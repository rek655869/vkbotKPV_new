import sqlite3
from functools import wraps
from logger import Logger


def connect(to_commit: bool):
    def decorator(func):
        def wrapped(self, *args, **kwargs):
            with sqlite3.connect(self.name) as connection:
                cursor = connection.cursor()
                result = func(self, cursor, *args, **kwargs)
                if to_commit:
                    connection.commit()
                cursor.close()
            return result
        return wrapped
    return decorator


class DBManager:
    def __init__(self, name: str):
        self.name = name
        self.logger = Logger.get(__name__)

    @connect(0)
    def fetchone(self, cursor, sql):
        cursor.execute(sql + ';')
        return cursor.fetchone()

    @connect(0)
    def fetchall(self, cursor, sql):
        cursor.execute(sql + ';')
        return cursor.fetchall()

    @connect(1)
    def add(self, cursor, sql):
        cursor.execute(sql + ';')


    # def get_actions(self):
    #     """Получение списка деятельностей"""
    #     sql = 'SELECT DISTINCT name FROM actions'
    #     return self.fetchall(sql)


    def set_command(self, user_id: int, command_name: str):
        """
        Добавление пользователя в таблицу, обозначающую в какой команде он находится
        :param user_id: id пользователя
        :param command_name: название команды
        """
        sql = 'UPDATE users SET command = "{}" WHERE vk_id = {}'.format(command_name, user_id)
        self.add(sql)

    def get_command(self, user_id: int) -> str or None:
        """
        Получение команды, в которой находится пользователь
        :param user_id: id пользователя
        """
        sql = "SELECT command FROM users WHERE vk_id = {}".format(user_id)
        result = self.fetchone(sql)
        if not result:
            return None
        return result[0]

    def upd_step(self, user_id: int, command: str, step: str):
        """
        Обновление шага, на котором остановился пользователь
        :param user_id: id пользователя
        :param command: название команды (класса)
        :param step: шаг
        """
        sql = 'INSERT INTO {} (vk_id, step) VALUES({}, "{}") ON CONFLICT(vk_id) DO UPDATE SET step = excluded.step'\
            .format(command, user_id, step)
        self.add(sql)

    def get_step(self, user_id: int, command: str) -> str or None:
        """
        Получение шага, на котором находится пользователь
        :param user_id: id пользователя
        :param command: название команды (класса)
        :return: шаг
        """
        sql = "SELECT step FROM {} WHERE vk_id = {}".format(command, user_id)
        result = self.fetchone(sql)
        if not result:
            return None
        return result[0]

    def add_command(self, user_id: int, command: str):
        """
        Добавление названия запущенной команды
        :param user_id: id пользователя
        :param command: название команды (класса)
        """
        if command:
            sql = 'UPDATE users SET command = "{}" WHERE vk_id = {}'.format(command, user_id)
        else:
            sql = 'UPDATE users SET command = NULL WHERE vk_id = {}'.format(user_id)
        self.add(sql)


    def del_command(self, user_id: int, command: str):
        """
        Удаление всех данных о шагах пользователя в определённой таблице (команде)
        :param user_id: id пользователя
        :param command: название команды
        """
        sql = 'DELETE FROM {} WHERE vk_id = {}'.format(command, user_id)
        self.add(sql)

    def add_msg_to_del(self, user_id: int, message_id: int):
        """
        Добавление сообщения в список для удаления
        :param user_id: id пользователя
        :param message_id: id сообщения
        """
        sql = 'INSERT INTO msg_to_del ("vk_id", "message_id") VALUES ({}, {})' \
            .format(user_id, message_id)
        self.add(sql)

    def get_msg_to_del(self, user_id: int) -> tuple or None:
        """
        Получение сообщений, которые надо удалить
        :param user_id: id пользователя
        :return: id сообщений
        """
        sql = "SELECT message_id FROM msg_to_del WHERE vk_id = {}".format(user_id)
        result = self.fetchall(sql)
        if not result:
            return None
        lst = []
        for msg in result:
            lst.append(msg[0])
        return lst


    def del_msg_to_del(self, user_id: int):
        """
        Удаление сообщений из списка
        :param user_id: id пользователя
        """
        sql = 'DELETE FROM msg_to_del WHERE vk_id = {}'.format(user_id)
        self.add(sql)


    def get_users(self) -> list:
        """
        Получение пользователей из БД
        :return: очередная строка из БД
        """
        sql = 'SELECT * FROM users'
        return self.fetchall(sql)
