from command_manager import Command, Access
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from sqlite3 import IntegrityError
import re


class AddReminder(Command):
    keys = ["добавить напоминание"]

    def process(self, message):
        user_id = message['from_id']
        step = self.bot.db.get_step(user_id, self.__class__.__name__)

        if step is None:
            self.start(user_id)
        elif step == "name":
            self.set_name(user_id, message['text'])
        elif step == "time" and ("всё" in message['text'].lower() or "все" in message['text'].lower()):
            self.get_all(user_id)
        elif step == "time":
            self.get_times(user_id, message['text'])
        elif step == "remind_time":
            self.add_reminder(user_id, message['text'])
        else:
            msg = self.bot.vk.send(user_id, "Некорректный ввод")
            self.bot.db.add_msg_to_del(user_id, msg)


    def start(self, user_id: int):
        text = "Существующие деятельности:\n"
        # получаем список деятельностей
        actions_list = self._get_actions()
        if actions_list:
            for _ in range(0, len(actions_list)):
                elem = actions_list[0]
                text += f"• {elem[0]} [{elem[1]}]\n"
                actions_list.pop(0)

        msg = self.bot.vk.send(user_id, text)
        msg = self.bot.vk.send(user_id, "Введите название деятельности, для которой хотите установить напоминание",
                               keyboard=self.exit())
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "name")
        self.bot.db.add_command(user_id, self.__class__.__name__)


    def set_name(self, user_id: int, text: str):
        text = text.strip()
        actions_list = [x[0] for x in self._get_actions_names()]
        if text.lower() not in actions_list:
            msg = self.bot.vk.send(user_id, "Деятельность не найдена, попробуйте скопировать её название из списка выше (только название, без времени)",
                                   keyboard=self.exit())
            self.bot.db.add_msg_to_del(user_id, msg)
        else:
            self._add_name(user_id, text)
            msg = self.bot.vk.send(user_id,
                                   'Введите время проведения деятельности в формате 00:00, можно ввести сразу несколько через '
                                   'запятую. Или же можно написать просто "все"',
                                   keyboard=self.exit())
            self.bot.db.add_msg_to_del(user_id, msg)
            self.bot.db.upd_step(user_id, self.__class__.__name__, "time")


    def get_all(self, user_id: int):
        name = self._get_name(user_id)
        actions_list = self._get_actions_by_name(name)
        times = []
        if actions_list:
            for elem in actions_list:
                times.append(elem[1])
        self._add_time(user_id, times)
        msg = self.bot.vk.send(user_id, "За сколько минут напоминать? (5 или 10)")
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "remind_time")


    def get_times(self, user_id: int, text: str):
        times = text.replace(" ", "")
        new_times = []
        for time in times.split(","):
            try:
                re.match(r'([0-1]\d|[20-23]{2}):([0-5]\d)', time).group()
                new_times.append(time)
            except AttributeError:
                msg = self.bot.vk.send(user_id, f"{time} введено некорректно")
                self.bot.db.add_msg_to_del(user_id, msg)
                continue
        self._add_time(user_id, new_times)
        msg = self.bot.vk.send(user_id, "За сколько минут напоминать? (5 или 10)")
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "remind_time")


    def add_reminder(self, user_id: int, text: str):
        try:
            remind_time = re.match(r'\d+', text).group()
            if remind_time != '10' and remind_time != '5':
                raise AttributeError
        except AttributeError:
            msg = self.bot.vk.send(user_id, "Некорректный ввод")
            self.bot.db.add_msg_to_del(user_id, msg)
            return

        name = self._get_name(user_id)
        times = self._get_time(user_id).split(", ")
        actions_list = self._get_actions_by_name(name)
        for elem in actions_list:
            if elem[1] in times:
                try:
                    self._add_action(user_id, elem[0], int(remind_time))
                except IntegrityError:
                    msg = self.bot.vk.send(user_id, f"{elem[1]} уже добавлено")
                    self.bot.db.add_msg_to_del(user_id, msg)
        msg = self.bot.vk.send(user_id, "Внесено!")
        self.bot.event_manager.command_manager.exit(user_id)


    def _get_name(self, user_id: int):
        sql = 'SELECT name FROM {} WHERE vk_id = {}'.format(self.__class__.__name__, user_id)
        result = self.bot.db.fetchone(sql)
        return result[0]


    def _get_time(self, user_id: int):
        sql = 'SELECT time FROM {} WHERE vk_id = {}'.format(self.__class__.__name__, user_id)
        result = self.bot.db.fetchone(sql)
        return result[0]


    def _get_actions(self):
        sql = "SELECT name, GROUP_CONCAT(time, ',') AS times FROM actions GROUP BY name"
        result = self.bot.db.fetchall(sql)
        if result:
            return result
        else:
            return None


    def _get_actions_by_name(self, name: str):
        sql = 'SELECT id, time FROM actions WHERE name = "{}"'.format(name)
        result = self.bot.db.fetchall(sql)
        if result:
            return result
        else:
            return None


    def _get_actions_names(self):
        sql = "SELECT DISTINCT name FROM actions"
        result = self.bot.db.fetchall(sql)
        if result:
            return result
        else:
            return None


    def _add_name(self, user_id: int, text: str):
        sql = 'UPDATE {} SET name = "{}" WHERE vk_id = {}'.format(self.__class__.__name__, text, user_id)
        self.bot.db.add(sql)


    def _add_time(self, user_id: int, times: list):
        sql = 'UPDATE {} SET time = "{}" WHERE vk_id = {}'.format(self.__class__.__name__, ', '.join(times), user_id)
        self.bot.db.add(sql)

    def _add_action(self, user_id: int, act_id: int, remind_time: int):
        sql = 'INSERT INTO reminders ("vk_id", "action_id", "remind_time") VALUES ({}, {}, {})'\
            .format(user_id, act_id, remind_time)
        self.bot.db.add(sql)

