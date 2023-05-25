from command_manager import Command, Access
import re


class DelAction(Command):
    keys = ["удалить деятельность"]
    access = Access.ADMIN

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
        text = "Существующие деятельности:\n"
        # получаем список деятельностей
        actions_list = self._get_actions()
        if actions_list:
            for _ in range(0, len(actions_list)):
                elem = actions_list[0]
                text += f"• {elem[0]} [{elem[1]}]\n"
                actions_list.pop(0)

        msg = self.bot.vk.send(user_id, text)
        msg = self.bot.vk.send(user_id, "Введите только название удаляемой деятельности (например, охота)",
                               keyboard=self.exit())
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "name")
        self.bot.db.add_command(user_id, self.__class__.__name__)


    def set_name(self, user_id: int, text: str):
        text = text.strip()
        self._add_name(user_id, text)
        msg = self.bot.vk.send(user_id,
                               'Введите время проведения деятельности в формате 00:00, можно ввести сразу несколько через '
                               'запятую. Если же нужно удалить деятельность полностью, введите "все"',
                               keyboard=self.exit())
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "time")


    def del_all(self, user_id: int):
        name = self._get_name(user_id)
        self._del_action(name)
        self.bot.logger.info(f"Пользователь {user_id} удалил деятельность {name}")
        msg = self.bot.vk.send(user_id, "Удалено!")
        self.bot.event_manager.command_manager.exit(user_id)


    def del_times(self, user_id: int, text: str):
        name = self._get_name(user_id)
        times = text.replace(" ", "")
        for time in times.split(","):
            try:
                re.match(r'([0-1]\d|[20-23]{2}):([0-5]\d)', time).group()
            except AttributeError:
                msg = self.bot.vk.send(user_id, f"{time} введено некорректно")
                self.bot.db.add_msg_to_del(user_id, msg)
                continue
            self._del_time(name, time)
        self.bot.logger.info(f"Пользователь {user_id} удалил некоторое время в деятельности {name}")
        msg = self.bot.vk.send(user_id, "Удалено!")
        self.bot.event_manager.command_manager.exit(user_id)


    def _get_actions(self):
        sql = "SELECT name, GROUP_CONCAT(time, ',') AS times FROM actions GROUP BY name"
        result = self.bot.db.fetchall(sql)
        if result:
            return result
        else:
            return None


    def _add_name(self, user_id: int, text: str):
        sql = 'UPDATE {} SET name = "{}" WHERE vk_id = {}'.format(self.__class__.__name__, text, user_id)
        self.bot.db.add(sql)


    def _get_name(self, user_id: int):
        sql = 'SELECT name FROM {} WHERE vk_id = {}'.format(self.__class__.__name__, user_id)
        result = self.bot.db.fetchone(sql)
        return result[0]


    def _del_action(self, name: str):
        sql = 'DELETE FROM actions WHERE name = "{}"'.format(name)
        self.bot.db.add(sql)


    def _del_time(self, name: str, time: str):
        sql = 'DELETE FROM actions WHERE name = "{}" AND time = "{}"'.format(name, time)
        self.bot.db.add(sql)
