import os
from enum import Enum
import pyclbr
import glob
from importlib import import_module

import commands.admin.applicant
from logger import Logger
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class Access(Enum):
    ADMIN = ['creator', 'administrator']
    EDITOR = ['creator', 'administrator', 'moderator']
    ANY = ['creator', 'administrator', 'editor', 'moderator', 'advertiser', 'user']


class Command:
    # массив строк с вариациями текста, по которым будет вызвана команда
    keys: list = []
    # уровень доступа
    access = Access.ANY
    # описание, показываемое при вызове команды "помощь"
    description = ''

    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger.get(__name__)

    def process(self, message):
        pass

    @staticmethod
    def exit() -> str:
        keyboard = VkKeyboard()
        keyboard.add_callback_button(label="Выйти", color=VkKeyboardColor.NEGATIVE, payload=["exit"])
        return keyboard.get_keyboard()


class Commander:
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger.get(__name__)
        self._load_commands()
        self.logger.info("Команды добавлены")

    def _load_commands(self):
        self.commands = []

        cmd_submodules = dict()
        # Ищем все подмодули и все классы в них без импорта самих подмодулей.
        for root, dirs, files in os.walk("commands", topdown=False):
            abs_search_path = os.path.join(os.path.dirname(__file__), root, '*.py')
            for path in glob.glob(abs_search_path):
                submodule_name = os.path.basename(path)[:-3]  # -3 из-за '.py'
                all_classes = pyclbr.readmodule("{0}.{1}".format(root.replace(os.path.sep, '.'), submodule_name))
                # Ищем в подмодуле класс, наследующий Command.
                for _, cls in all_classes.items():
                    if 'Command' in cls.super:
                        submodule = import_module(cls.module)  # импортируем подмодуль по имени
                        class_instance = getattr(submodule, cls.name)(self.bot)
                        self.commands.append(class_instance)

    def handler(self, message):
        text = message['text'].lower()
        user_id = message['from_id']
        post = self.bot.vk.get_post(user_id)

        if text == 'exit':
            self.exit(user_id, post)

        if not post:
            for command in self.commands:
                if command.__class__.__name__ == 'Intro':
                    return command.process(message)

        self.del_last_messages(user_id)

        current_command = self.bot.db.get_command(user_id)
        if current_command:
            for command in self.commands:
                if current_command == command.__class__.__name__:
                    return command.process(message)
        else:
            for command in self.commands:
                if text in command.keys and post in command.access.value:
                    return command.process(message)

    def event_handler(self, event):
        payload = event['payload']
        user_id = event['user_id']
        self.del_last_messages(user_id)

        if payload[0] == 'accept':
            commands.admin.applicant.accept(self.bot, payload, user_id, event['event_id'])
        elif payload[0] == 'reject':
            commands.admin.applicant.reject(self.bot, payload, user_id, event['event_id'])
        else:
            self.bot.vk.event_answer(event['event_id'], user_id)
            message = {'from_id': user_id, 'text': payload[0]}
            self.handler(message)

    def menu(self, user_id: int):
        post = self.bot.vk.get_post(user_id)
        kb = VkKeyboard(one_time=True)
        if post in Access.ADMIN:
            kb.add_callback_button(label='Добавить деятельность', color=VkKeyboardColor.PRIMARY,
                                   payload=['Добавить деятельность'])
            kb.add_callback_button(label='Удалить деятельность', color=VkKeyboardColor.PRIMARY,
                                   payload=['Удалить деятельность'])
            kb.add_line()
            kb.add_callback_button(label='Оставить в группе', color=VkKeyboardColor.PRIMARY,
                                   payload=['оставить'])
        kb.add_callback_button(label='Добавить напоминание', color=VkKeyboardColor.SECONDARY,
                               payload=['Добавить напоминание'])
        kb.add_callback_button(label='Мои напоминания', color=VkKeyboardColor.SECONDARY,
                               payload=['Мои напоминания'])
        kb.add_line()
        kb.add_callback_button(label='Удалить напоминание', color=VkKeyboardColor.SECONDARY,
                               payload=['Удалить напоминание'])
        kb = kb.get_keyboard()
        msg = self.bot.vk.send(user_id, "Выберите действие:",
                               keyboard=kb)
        self.bot.db.add_msg_to_del(user_id, msg)

    def exit(self, user_id: int):
        """
        Выход из текущей команды
        :param user_id: id пользователя
        """
        if self.bot.vk.get_post(user_id):
            current_command = self.bot.db.get_command(user_id)
            self.bot.db.add_command(user_id, "")
            self.bot.db.del_command(user_id, current_command)
            self.menu(user_id)
        else:
            self.bot.db.del_command(user_id, 'Intro')


    def del_last_messages(self, user_id: int):
        # удаляем предыдущие сообщения
        msg_to_del = self.bot.db.get_msg_to_del(user_id)
        if msg_to_del:
            self.bot.vk.del_message(user_id, msg_to_del)
            self.bot.db.del_msg_to_del(user_id)
