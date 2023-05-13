import vk_api
import time
import re
from requests.exceptions import ReadTimeout
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.vk_api import VkUserPermissions
from logger import Logger
import json


class SecureVkLongPoll(VkBotLongPoll):
    """Обработка разрыва соединения от лонгпула"""
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except ReadTimeout:
                time.sleep(5)


class VkApiManager:
    """Класс, облегчающий взаимодействие с API ВК"""
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger.get(__name__)
        self.group_id = bot.config.VK.group_id
        self._vk_session = vk_api.VkApi(token=bot.config.VK.token)

        # токены разных уровней
        self.group = self._vk_session.get_api()
        self.service = vk_api.VkApi(token=bot.config.VK.service_token).get_api()
        self.admin = vk_api.VkApi(token=bot.config.VK.access_token).get_api()

        self._check_access_token()

        self.longpoll = SecureVkLongPoll(self._vk_session, self.group_id)

        self.logger.info("VkApiManager запущен")
        # LongPollServer = vk.groups.getLongPollServer(group_id=group_id)
        # key, server, ts = LongPollServer['key'], LongPollServer['server'], LongPollServer['ts']
        # config = {'key': key, 'server': server, 'ts': ts}

    def _check_access_token(self):
        """Проверка работоспособности токена администратора"""
        try:
            self.admin.groups.getInvitedUsers(group_id=self.group_id, count=1)
        except vk_api.exceptions.ApiError as error:
            if error.code == 5 or error.code == 15:
                self.logger.warning('Не удаётся применить access_token. Попытка получения...')
                self._get_access_token()
            else:
                raise error

    def _get_access_token(self):
        """Получение токена администратора при его отсутствии"""
        scope = VkUserPermissions.PAGES | VkUserPermissions.STATUS | VkUserPermissions.OFFLINE | VkUserPermissions.GROUPS
        link = 'https://oauth.vk.com/oauth/authorize?' \
               'client_id=7976922&' \
               f'scope={scope}&' \
               'redirect_uri=https://oauth.vk.com/blank.html&' \
               'display=page&' \
               'response_type=token&' \
               'revoke=1'

        rek = vk_api.VkApi(token=self.bot.config.VK.rek_access_token).get_api()
        managers = rek.groups.getMembers(group_id=self.group_id, filter='managers')
        admin_id = [user['id'] for user in managers['items'] if user['role'] == 'administrator' or user['role'] == 'creator'][0] #and user['id'] != 478936081
        temp_longpoll = VkBotLongPoll(self._vk_session, self.group_id)

        short_link = self.group.utils.getShortLink(url=link)['short_url']
        self.send(admin_id, 'С доступом что-то не то. Пожалуйста, перейдите по ссылке ниже для выдачи разрешения на '
                  'выполнение действий от вашего имени (просмотр времени захода других пользователей, принятие и '
                  'удаление из группы).\n'
                  'Когда перейдете на страницу с предостережением о краже страницы, скопируйте всю(!) адресную строку '
                  'и отправьте сюда.\n'
                  'Все данные хранятся конфиденциально, сообщение с токеном будет удалено сразу после получения '
                  '(только со стороны группы). В целях безопасности Вам также рекомендуется удалить сообщение в диалоге.\n'
                  f'>> {short_link} <<')
        self.logger.warning(f'Ссылка для получения токена отправлена администратору (id={admin_id}).')

        while True:
            for event in temp_longpoll.check():
                if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                    if event.message['from_id'] == admin_id:
                        text = event.message['text']
                        token = re.findall(r'(?<=access_token=).+(?=&expires_in)', text)[0]

                        from configparser import ConfigParser
                        config = ConfigParser()
                        config.read('config.ini')
                        config.set('VK', 'access_token', token)
                        with open('config.ini', 'w') as f:
                            config.write(f)

                        self.admin = vk_api.VkApi(token=token).get_api()
                        self.logger.warning('Получен новый токен')
                        self.send(admin_id, 'Токен получен')
                        exit(1)

    def get_post(self, user_id: int) -> str or None:
        managers = self.admin.groups.getMembers(group_id=self.group_id, filter='managers')['items']
        for user in managers:
            if user['id'] == user_id:
                return user['role']
        user = self.group.groups.isMember(group_id=self.group_id, user_id=user_id)
        if not user:
            return None
        return 'user'

    def send(self, user_id: int, message: str = None, keyboard: str = None,
             attachment: str = None, forward_messages: str = None) -> int:
        """
        Отправка сообщения
        :param user_id: id получателя
        :param message: текст сообщения
        :param keyboard: клавиатура бота (json)
        :param attachment: вложения
        :param forward_messages: id пересылаемых сообщений через запятую
        :return: id отправленного сообщения
        """
        try:
            message_id = self.group.messages.send(user_id=user_id, random_id=get_random_id(), message=message,
                                                  keyboard=keyboard, forward_messages=forward_messages)
            return message_id

        except vk_api.exceptions.ApiError as e:
            if e.code == 901:
                pass
            else:
                raise e

    def event_answer(self, event_id: int, user_id: int):
        """
        Отправка ответа на событие
        :param event_id: id события
        :param user_id: id пользователя, в диалоге с которым произошло событие
        """
        self.group.messages.sendMessageEventAnswer(event_id=event_id, user_id=user_id, peer_id=user_id)


    def show_snackbar(self, event_id: int, user_id: int, text: str):
        event = json.dumps({"type": "show_snackbar", "text": text})
        self.group.messages.sendMessageEventAnswer(event_id=event_id, user_id=user_id,
                                                   peer_id=user_id, event_data=event)


    def del_message(self, user_id: int, message_ids: str or list or tuple):
        """
        Удаление сообщения
        :param user_id: id пользователя
        :param message_ids: id сообщений (одно или несколько)
        """
        if (isinstance(message_ids, list) or isinstance(message_ids, tuple)) and len(message_ids) > 1:
            message_ids = ','.join(map(str, message_ids))
        try:
            self.group.messages.delete(message_ids=message_ids, group_id=self.group_id,
                                       delete_for_all=1, peer_id=user_id)
        except vk_api.exceptions.ApiError as e:
            if e.code == 15 or e.code == 924:  # если не удаётся удалить сообщение
                pass
            else:
                raise e


    def get_editors(self) -> tuple:
        managers = self.admin.groups.getMembers(group_id=self.group_id, filter='managers')['items']
        editors = []
        times_seen = {}
        for user in managers:
            if user['role'] == 'editor':
                editors.append(user['id'])
                last_seen = self.admin.users.get(user_ids=user, fields='last_seen')[0]['last_seen']['time']
                if last_seen:
                    times_seen.update({last_seen: user})
        if not times_seen:
            for user in managers:
                if user['role'] == 'administrator':
                    editors.append(user['id'])
                    last_seen = self.admin.users.get(user_ids=user, fields='last_seen')[0]['last_seen']['time']
                    if last_seen:
                        times_seen.update({last_seen: user})
        return times_seen[max(times_seen)], editors


    def save_page(self, html, page_id):
        self.admin.pages.save(text=html, page_id=page_id, group_id=self.group_id)
