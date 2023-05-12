from command_manager import Command
import re


class DelReminder(Command):
    keys = ["удалить напоминание"]

    def process(self, message):
        user_id = message['from_id']
        step = self.bot.db.get_step(user_id, self.__class__.__name__)

        if step is None:
            self.start(user_id)
        elif step == "name":
            self.set_name(user_id, message['text'])
        elif step == "time" and ("всё" in message['text'].lower() or "все" in message['text'].lower()):
            self.del_all(user_id)
        elif step == "time":
            self.del_times(user_id, message['text'])
        else:
            msg = self.bot.vk.send(user_id, "Некорректный ввод")
            self.bot.db.add_msg_to_del(user_id, msg)

    def start(self, user_id: int):
        msg = self.bot.vk.send(user_id, "Введите только название удаляемой деятельности",
                               keyboard=self.exit())
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "name")
        self.bot.db.add_command(user_id, self.__class__.__name__)


    def set_name(self, user_id: int, text: str):
        text = text.strip()
        self._add_name(user_id, text)
        msg = self.bot.vk.send(user_id,
                               'Введите время проведения деятельности в формате 00:00, можно ввести сразу несколько через '
                               'запятую. Если же нужно удалить напоминания о деятельности полностью, введите "все"',
                               keyboard=self.exit())
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "time")


    def del_all(self, user_id: int):
        name = self._get_name(user_id)
        actions_list = self._get_actions_by_name(name)
        if actions_list:
            for elem in actions_list:
                self._del_action(user_id, elem[0])
        msg = self.bot.vk.send(user_id, "Удалено!")
        self.bot.event_manager.command_manager.exit(user_id)


    def del_times(self, user_id: int, text: str):
        name = self._get_name(user_id)
        times = text.replace(" ", "")
        actions_list = self._get_actions_by_name(name)
        for time in times.split(","):
            try:
                re.match(r'([0-1]\d|[20-23]{2}):([0-5]\d)', time).group()
            except AttributeError:
                msg = self.bot.vk.send(user_id, f"{time} введено некорректно")
                self.bot.db.add_msg_to_del(user_id, msg)
                continue
            for elem in actions_list:
                if time == elem[1]:
                    self._del_action(user_id, elem[0])
        msg = self.bot.vk.send(user_id, "Удалено!")
        self.bot.event_manager.command_manager.exit(user_id)


    def _add_name(self, user_id: int, text: str):
        sql = 'UPDATE {} SET name = "{}" WHERE vk_id = {}'.format(self.__class__.__name__, text, user_id)
        self.bot.db.add(sql)


    def _get_name(self, user_id: int):
        sql = 'SELECT name FROM {} WHERE vk_id = {}'.format(self.__class__.__name__, user_id)
        result = self.bot.db.fetchone(sql)
        return result[0]

    def _get_actions_by_name(self, name: str):
        sql = 'SELECT id, time FROM actions WHERE name = "{}"'.format(name)
        result = self.bot.db.fetchall(sql)
        if result:
            return result
        else:
            return None


    def _del_action(self, user_id: int, act_id: int):
        sql = 'DELETE FROM reminders WHERE vk_id = {} AND action_id = {}'.format(user_id, act_id)
        self.bot.db.add(sql)

