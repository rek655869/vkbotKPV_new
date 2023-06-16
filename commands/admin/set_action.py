from command_manager import Command, Access
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import re


class SetAction(Command):
    keys = ["добавить деятельность"]
    access = Access.ADMIN

    def process(self, message):
        user_id = message['from_id']
        step = self.bot.db.get_step(user_id, self.__class__.__name__)

        if step is None:
            self.start(user_id)
        elif step == "name":
            self.set_name(user_id, message['text'])
        elif step == "time":
            self.set_time(user_id, message['text'])
        elif step == "checking" and "готово" in message['text'].lower():
            self.set_action(user_id)
        else:
            msg = self.bot.vk.send(user_id, "Некорректный ввод")
            self.bot.db.add_msg_to_del(user_id, msg)


    def start(self, user_id: int):
        msg = self.bot.vk.send(user_id, "Введите название добавляемой деятельности",
                               keyboard=self.exit())
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "name")
        self.bot.db.add_command(user_id, self.__class__.__name__)

    def set_name(self, user_id: int, text: str):
        text = text.strip().lower()
        self._add_name(user_id, text)
        msg = self.bot.vk.send(user_id,
                               "Введите время проведения деятельности в формате 00:00, можно ввести сразу несколько через запятую",
                               keyboard=self.exit())
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "time")

    def set_time(self, user_id: int, text: str):
        times = text.replace(" ", "")
        correct_times = []
        for time in times.split(","):
            try:
                re.match(r'([0-1]\d|[20-23]{2}):([0-5]\d)', time).group()
            except AttributeError:
                msg = self.bot.vk.send(user_id, f"{time} введено некорректно")
                self.bot.db.add_msg_to_del(user_id, msg)
                continue
            correct_times.append(time)
        correct_times = ', '.join(correct_times)
        self._add_time(user_id, correct_times)
        name = self._get_name(user_id)

        kb = VkKeyboard(one_time=True)
        kb.add_callback_button(label='Готово', color=VkKeyboardColor.POSITIVE, payload=["Готово"])
        kb.add_callback_button(label='Отмена', color=VkKeyboardColor.NEGATIVE, payload=['exit'])
        kb = kb.get_keyboard()
        msg = self.bot.vk.send(user_id, f"Проверьте введённые данные:\n"
                                        f"Название: {name}\n"
                                        f"Время проведения: {correct_times}",
                               keyboard=kb)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "checking")


    def set_action(self, user_id: int):
        name = self._get_name(user_id)
        times = self._get_time(user_id).split(",")
        for time in times:
            time = time.strip()
            if time:
                if not self._check_action(name, time):
                    self._set_action(name, time)
                else:
                    msg = self.bot.vk.send(user_id, f"{name} {time} уже существует")
        self.bot.logger.info(f"Пользователь {user_id} добавил деятельность {name}")
        msg = self.bot.vk.send(user_id, "Внесено!")
        self.bot.event_manager.command_manager.exit(user_id)


    def _add_name(self, user_id: int, text: str):
        sql = 'UPDATE {} SET name = "{}" WHERE vk_id = {}'.format(self.__class__.__name__, text, user_id)
        self.bot.db.add(sql)

    def _add_time(self, user_id: int, text: str):
        sql = 'UPDATE {} SET time = "{}" WHERE vk_id = {}'.format(self.__class__.__name__, text, user_id)
        self.bot.db.add(sql)

    def _get_name(self, user_id: int):
        sql = 'SELECT name FROM {} WHERE vk_id = {}'.format(self.__class__.__name__, user_id)
        result = self.bot.db.fetchone(sql)
        return result[0]

    def _get_time(self, user_id: int):
        sql = 'SELECT time FROM {} WHERE vk_id = {}'.format(self.__class__.__name__, user_id)
        result = self.bot.db.fetchone(sql)
        return result[0]

    def _set_action(self, name: str, time: str):
        sql = 'INSERT INTO actions ("name", "time") VALUES ("{}", "{}")'.format(name, time)
        self.bot.db.add(sql)


    def _check_action(self, name: str, time: str):
        sql = 'SELECT * FROM actions WHERE name = "{}" AND time = "{}"'.format(name, time)
        if self.bot.db.fetchone(sql):
            return 1
        return 0
