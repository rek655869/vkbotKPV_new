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
        self.vk.get_editors()



if __name__ == '__main__':
    Bot()
