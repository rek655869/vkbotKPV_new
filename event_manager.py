import threading
from vk_api.bot_longpoll import VkBotEventType
from command_manager import Commander
from logger import Logger
from errors_handler import ErrorHandler


class EventManager:
    """Обработчик событий"""
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger.get(__name__)
        self.command_manager = Commander(self.bot)
        threading.Thread(target=self._start, name='event-listening', daemon=True).start()

    @ErrorHandler.main_errors_handler
    def _start(self):
        self.logger.info("EventManager запущен")
        while True:
            for event in self.bot.vk.longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
                    self.command_manager.handler(event.message)
                    continue
                elif event.type == VkBotEventType.MESSAGE_EVENT:
                    self.command_manager.event_handler(event.object)
                    continue
