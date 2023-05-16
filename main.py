from bestconfig import Config
from event_manager import EventManager
from vkapi_manager import VkApiManager
from database import DBManager
from mailing import Deliveryman
from update_pages import Updater
from logger import Logger
from cw_cookies import get_cookies


class Bot:
    """Основной класс, где происходит инициализация 'служб' бота"""
    def __init__(self):
        self.config = Config()
        self.logger = Logger.get(__name__)
        self.logger.info("Запуск...")

        self.cw = get_cookies()
        self.vk = VkApiManager(self)
        self.db = DBManager(self.config.DATABASE.name)
        self.event_manager = EventManager(self)
        self.deliveryman = Deliveryman(self)
        self.updater = Updater(self)

        self.logger.info(self.vk.get_editors())
        last_seen = self.vk.admin.users.get(user_ids=245866128, fields='last_seen, sex')
        self.logger.info(last_seen)



if __name__ == '__main__':
    Bot()
