from command_manager import Command, Access
import re


class LeaveUser(Command):
    keys = ["оставить"]
    access = Access.EDITOR

    def process(self, message):
        user_id = message['from_id']
        step = self.bot.db.get_step(user_id, self.__class__.__name__)

        if step is None:
            self.start(user_id)
        elif step == "cw_id":
            self.add_perm(user_id, message['text'])
        else:
            msg = self.bot.vk.send(user_id, "Некорректный ввод")
            self.bot.db.add_msg_to_del(user_id, msg)


    def start(self, user_id: int):
        msg = self.bot.vk.send(user_id, "Введите ID игрока на CatWar",
                               keyboard=self.exit())
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "cw_id")
        self.bot.db.add_command(user_id, self.__class__.__name__)


    def add_perm(self, user_id, text):
        cw_id = re.match(r'\d+', text).group()
        vk_ids = self._get_id(cw_id)
        for vk_id in vk_ids:
            self._add_perm_vk_id(vk_id, cw_id)
        msg = self.bot.vk.send(user_id, "Внесено!")
        self.bot.event_manager.command_manager.exit(user_id)


    def _get_id(self, cw_id):
        sql = 'SELECT vk_id FROM users WHERE cw_id={}'.format(cw_id)
        res = self.bot.db.fetchall(sql)
        return [x[0] for x in res]

    def _add_perm_vk_id(self, user_id, cw_id):
        sql = 'INSERT INTO with_perm (vk_id, cw_id) VALUES ({}, {})'.format(user_id, cw_id)
        self.bot.db.add(sql)
