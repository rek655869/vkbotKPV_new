from command_manager import Command, Access
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class MyReminders(Command):
    keys = ["мои напоминания"]

    def process(self, message):
        user_id = message['from_id']
        user_actions = self._get_user_actions(user_id)

        if not user_actions:
            msg = self.bot.vk.send(user_id, "Напоминаний нет")
            return

        text = "Установленные напоминания:\n"
        action_dict = {}
        for action_id in user_actions:
            try:
                name, time = self._get_actions(action_id)
            except TypeError:
                self._del_reminder(action_id)
                continue
            if name in action_dict.keys():
                temp = action_dict.get(name)
                if not isinstance(temp, list):
                    temp = [temp]
                temp.append(time)
            else:
                temp = [time]
            action_dict.update({name: temp})
        for name, times in action_dict.items():
            text += f"• {name} [{', '.join(times)}]\n"

        msg = self.bot.vk.send(user_id, text)


    def _get_user_actions(self, user_id: int):
        sql = 'SELECT action_id FROM reminders WHERE vk_id = {}'.format(user_id)
        result = self.bot.db.fetchall(sql)
        if result:
            result1 = [x[0] for x in result]
            return result1
        else:
            return None


    def _get_actions(self, action_id):
        sql = "SELECT name, time FROM actions WHERE id = {}".format(action_id)
        result = self.bot.db.fetchone(sql)
        return result

    def _del_reminder(self, action_id):
        sql = 'DELETE FROM reminders WHERE action_id = {}'.format(action_id)
        self.bot.db.add(sql)
