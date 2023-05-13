from command_manager import Command
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import re
from bs4 import BeautifulSoup
from threading import Timer


class Intro(Command):

    def process(self, message):
        user_id = message['from_id']
        step = self.bot.db.get_step(user_id, self.__class__.__name__)

        if step is None:
            self.start(user_id)
        elif step == "cw_id":
            if not self.get_id(user_id, message['text']):
                self.checking(user_id)
        elif step == "kitten_name":
            self.get_kitten_name(user_id, message['text'])
            self.checking(user_id)
        elif step == "checking" and "далее" in message['text'].lower():
            self.ask_for_screen(user_id)
        elif step == "send_form":
            forward_msg = self.end(user_id, message)
            if forward_msg:
                self.send_to_editor(user_id, forward_msg)
        elif step == "waiting":
            self.bot.vk.send(user_id, 'Заявка отправлена, осталось дождаться её одобрения',
                             keyboard=VkKeyboard.get_empty_keyboard())
        else:
            msg = self.bot.vk.send(user_id, "Некорректный ввод")
            self.bot.db.add_msg_to_del(user_id, msg)



    def start(self, user_id: int):
        msg = self.bot.vk.send(user_id, "Введите, пожалуйста, ваш ID на CatWar",
                               keyboard=VkKeyboard.get_empty_keyboard())
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "cw_id")
        self.bot.db.add_command(user_id, self.__class__.__name__)


    def get_id(self, user_id: int, text: str):
        try:
            cw_id = re.match(r'\d+', text).group()
        except AttributeError:
            msg = self.bot.vk.send(user_id, "Некорректный ввод")
            self.bot.db.add_msg_to_del(user_id, msg)
            return 1

        html = self.bot.cw.get(f'https://catwar.su/cat{cw_id}').text
        self.logger.warning(html)
        soup = BeautifulSoup(html, 'html.parser')
        profile = soup.find(attrs={"data-cat": cw_id})
        try:
            position = profile.find('i').text
        except AttributeError:
            msg = self.bot.vk.send(user_id, "Не удаётся определить должность")
            self.bot.db.add_msg_to_del(user_id, msg)
            return 1
        name = profile.find('big').text
        self._add_info(user_id, cw_id, name, position)

        if position == 'котёнок' or position == 'котенок':
            msg = self.bot.vk.send(user_id, "Введите, пожалуйста, имя, которое вы носили в прошлой жизни, "
                                            "будучи стражем/охотником",
                                   keyboard=self.exit())
            self.bot.db.add_msg_to_del(user_id, msg)
            self.bot.db.upd_step(user_id, self.__class__.__name__, "kitten_name")
            return 1


    def get_kitten_name(self, user_id: int, text: str):
        name = text.strip()
        self._add_kitten_name(user_id, name)


    def checking(self, user_id: int):
        profile = self._get_info(user_id)
        kb = VkKeyboard(one_time=True)
        kb.add_callback_button(label='Далее', color=VkKeyboardColor.POSITIVE, payload=["Далее"])
        kb.add_callback_button(label='Отмена', color=VkKeyboardColor.NEGATIVE, payload=['exit'])
        kb = kb.get_keyboard()
        text = f"Проверьте введённые данные:\nID: {profile[2]}\nИмя: {profile[3]}\nДолжность: {profile[4]}"
        if profile[5]:
            text += f"\nПрошлое имя: {profile[5]}"
        msg = self.bot.vk.send(user_id, text, keyboard=kb)
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "checking")

    def ask_for_screen(self, user_id: int):
        requests = self.bot.vk.admin.groups.getRequests(group_id=self.bot.vk.group_id)['items']
        if user_id not in requests:
            kb = VkKeyboard(one_time=True)
            kb.add_callback_button(label='Далее', color=VkKeyboardColor.POSITIVE, payload=["Готово"])
            kb.add_callback_button(label='Отмена', color=VkKeyboardColor.NEGATIVE, payload=['exit'])
            kb = kb.get_keyboard()
            msg = self.bot.vk.send(user_id, 'Пожалуйста, подайте заявку в группу',
                                   keyboard=kb)
            self.bot.db.add_msg_to_del(user_id, msg)
            self.bot.db.upd_step(user_id, self.__class__.__name__, "checking")
            return
        msg = self.bot.vk.send(user_id, 'Отправьте, пожалуйста, скриншот страницы "Мой кот"/"Моя кошка"',
                               keyboard=self.exit())
        self.bot.db.add_msg_to_del(user_id, msg)
        self.bot.db.upd_step(user_id, self.__class__.__name__, "send_form")


    def end(self, user_id: int, message) -> int:
        if not message['attachments']:
            msg = self.bot.vk.send(user_id, 'Отправьте, пожалуйста, скриншот страницы "Мой кот"/"Моя кошка"',
                                   keyboard=self.exit())
            self.bot.db.add_msg_to_del(user_id, msg)
            return
        forward_msg = message['id']
        msg = self.bot.vk.send(user_id, 'Заявка отправлена, осталось дождаться её одобрения',
                               keyboard=VkKeyboard.get_empty_keyboard())
        self.bot.db.upd_step(user_id, self.__class__.__name__, "waiting")
        return forward_msg


    def send_to_editor(self, user_id: int, forward_msg: int):
        last_editor, editors = self.bot.vk.get_editors()
        profile = self._get_info(user_id)
        self._send_form(last_editor, profile, user_id, forward_msg)
        t = Timer(600.0, self.send_all_editors, args=(last_editor, editors, profile, user_id, forward_msg))
        t.start()


    def send_all_editors(self, last_editor: int, editors: int, profile, user_id: int, forward_msg: int):
        value = self._get_info(user_id)
        if value:
            for editor in editors:
                if editor != last_editor:
                    self._send_form(editor, profile, user_id, forward_msg)


    def _send_form(self, editor_id: int, profile, user_id: int, forward_msg: int):
        text = f"{profile[3]} [{profile[2]}]"
        if profile[5]:
            text += f" (ранее {profile[5]})"
        text += f", {profile[4]}\n https://catwar.su/cat{profile[2]}"

        kb = VkKeyboard(inline=True)
        kb.add_callback_button(label='Принять', color=VkKeyboardColor.POSITIVE, payload=["accept", user_id, profile[3]])
        kb.add_callback_button(label='Отклонить', color=VkKeyboardColor.NEGATIVE, payload=["reject", user_id, profile[3]])
        kb = kb.get_keyboard()
        msg = self.bot.vk.send(editor_id, text, keyboard=kb, forward_messages=forward_msg)
        self._add_to_requests(msg, editor_id, user_id)


    def _add_cw_id(self, user_id: int, text: str):
        sql = 'UPDATE {} SET cw_id = {} WHERE vk_id = {}'.format(self.__class__.__name__, text, user_id)
        self.bot.db.add(sql)


    def _add_info(self, user_id: int, cw_id: int, name: str, position: str):
        sql = 'UPDATE {} SET `cw_id` = {}, `name` = "{}", position = "{}" WHERE vk_id = {}'\
            .format(self.__class__.__name__, cw_id, name, position, user_id)
        self.bot.db.add(sql)


    def _add_kitten_name(self, user_id: int, name: str):
        sql = 'UPDATE {} SET `last_name` = "{}" WHERE vk_id = {}'.format(self.__class__.__name__, name, user_id)
        self.bot.db.add(sql)


    def _get_info(self, user_id: int):
        sql = 'SELECT * FROM {} WHERE vk_id = {}'.format(self.__class__.__name__, user_id)
        return self.bot.db.fetchone(sql)


    def _add_to_requests(self, msg_id: int, editor_id: int, user_id: int):
        sql = 'INSERT INTO requests (message_id, editor_id, user_id) VALUES ({}, {}, {})'\
            .format(msg_id, editor_id, user_id)
        self.bot.db.add(sql)
