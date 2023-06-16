import threading
from logger import Logger
import functools
import traceback
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from bestconfig import Config
import vk_api
from vk_api.utils import get_random_id

logger = Logger.get(__name__)


def send_message(user_id: int, exc: str = None):
    vk = vk_api.VkApi(token=Config().VK.token).get_api()
    keyboard = VkKeyboard()
    keyboard.add_callback_button(label="Выйти", color=VkKeyboardColor.NEGATIVE, payload=["exit"])
    keyboard = keyboard.get_keyboard()
    vk.messages.send(user_id=user_id, random_id=get_random_id(),
                     message=exc or "Что-то пошло не так, попробуйте ещё раз. Если проблема не исчезнет, мы займёмся её решением",
                     keyboard=keyboard)


class ErrorHandler:

    @staticmethod
    def main_errors_handler(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            th_name = threading.current_thread().name
            while True:
                try:
                    func(*args, **kwargs)
                except Exception:
                    send_message(478936081, traceback.format_exc())
                    logger.warning(traceback.format_exc())
                    logger.warning(f'Падение потока {th_name}, перезапуск...')
        return wrapper

    @staticmethod
    def errors_handler(user_id: int):
        th_name = threading.current_thread().name
        send_message(user_id)
        logger.warning(traceback.format_exc())
        logger.warning(f'Маленькое падение потока {th_name}')
