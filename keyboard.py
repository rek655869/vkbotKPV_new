from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class Keyboard:
    """Варианты клавиатуры

    inline: кнопки в сообщении
    one_time: кнопки исчезают после отправки сообщения"""

    @staticmethod
    def exit() -> str:
        keyboard = VkKeyboard(inline=True)
        keyboard.add_button('Выйти', color=VkKeyboardColor.NEGATIVE)
        return keyboard.get_keyboard()

    @staticmethod
    def buttons(d: dict) -> str:
        keyboard = VkKeyboard(inline=True)
        for text, color in d.items():
            keyboard.add_callback_button(text, color=eval(f'VkKeyboardColor.{color}'), payload={'text': text})
        return keyboard.get_keyboard()

    @staticmethod
    def open_link(text: str, link: str) -> str:
        keyboard = VkKeyboard(inline=True)
        keyboard.add_openlink_button(text, link, payload={'text': text})
        return keyboard.get_keyboard()

    @staticmethod
    def anket() -> str:
        keyboard = VkKeyboard(inline=True)
        keyboard.add_callback_button('Да', color=VkKeyboardColor.POSITIVE)
        keyboard.add_callback_button('Нет', color=VkKeyboardColor.NEGATIVE)
        return keyboard.get_keyboard()

    @staticmethod
    def request(user_id) -> str:
        keyboard = VkKeyboard(inline=True)
        keyboard.add_button(f'Принять {user_id}', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button(f'Отклонить {user_id}', color=VkKeyboardColor.NEGATIVE)
        return keyboard.get_keyboard()