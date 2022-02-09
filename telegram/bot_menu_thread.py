from datetime import timedelta
from functools import reduce
from threading import Thread
from typing import Callable, Optional, Union

from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message, ReplyKeyboardRemove

from reminder import Reminder
from . import Telegram


class BotMenuThread(Thread):
    _reminders: dict[str, Reminder]
    _telegram: Telegram

    _keyboard_factories: dict[str, Callable[[], Union[ReplyKeyboardMarkup or ReplyKeyboardRemove]]]
    _menu_page_message_senders: dict[str, Callable[[], None]]
    _menu_handlers: dict[str, Callable[[Message], None]]
    _item_names: dict[str, str]

    _active_menu_page: str
    _chosen_reminder: Optional[Reminder]

    __last_user_message: Optional[Message]
    __last_bot_message: Optional[Message]
    __remove_keyboard_command: ReplyKeyboardRemove

    def __init__(self, bot: Telegram, reminders: dict[str, Reminder]):
        super().__init__()
        self._telegram = bot
        self._reminders = reminders
        self.__remove_keyboard_command = ReplyKeyboardRemove()

        self.__last_user_message = None
        self.__last_bot_message = None

        self._keyboard_factories = {
            'none': self.__no_keyboard,
            'main': self.__main_menu_keyboard,
            'text_hiding': self.__input_bool_keyboard,
            'reminder_selector': self.__reminder_selector_keyboard,
            'reminder_settings': self.__reminder_settings_keyboard,
            'reminder_messages_settings': self.__input_string_keyboard,
            'reminder_time_settings': self.__input_string_keyboard
        }
        self._menu_page_message_senders = {
            'none': self.__send_menu_exit_text,
            'main': self.__send_main_menu_text,
            'text_hiding': self.__send_toggle_message_hiding_text,
            'reminder_selector': self.__send_reminder_selector_text,
            'reminder_settings': self.__send_reminder_settings_text,
            'reminder_messages_settings': self.__send_reminder_configure_messages_text,
            'reminder_time_settings': self.__send_reminder_configure_time_text
        }
        self._menu_handlers = {
            'none': self.__no_menu_input_handler,
            'main': self.__main_menu_input_handler,
            'text_hiding': self.__text_hiding_input_handler,
            'reminder_selector': self.__reminder_selector_input_handler,
            'reminder_settings': self.__reminder_settings_input_handler,
            'reminder_messages_settings': self.__reminder_messages_settings_input_handler,
            'reminder_time_settings': self.__reminder_time_settings_input_handler
        }
        self._item_names = {
            'settings_command': '/settings',
            'text_hiding': 'Настройка скрытия текста',
            'reminder_selector': 'Настройка профилей',
            'reminder_configure_messages': 'Настройка списка напоминаний',
            'reminder_configure_time': 'Настройка временного интервала',
            'back': 'Назад',
            'cancel': 'Отмена',
            'exit': 'Закрыть настройки',
            'True': 'Да',
            'False': 'Нет',
            'incorrect_input': 'Некорректный ввод. Выбери из списка:'
        }
        self._active_menu_page = 'none'

    def run(self):
        self._telegram.bot.register_message_handler(self.__generic_message_handler, content_types=['text'])
        self._telegram.bot.infinity_polling(skip_pending=True)

    def __send(self, message) -> Message:
        keyboard_command = self._keyboard_factories[self._active_menu_page]()
        new_bot_message = self._telegram.send(message, hide_text=False, keyboard_markup=keyboard_command)
        self.last_bot_message = new_bot_message
        return new_bot_message

    def __delete(self, message: Message):
        if type(message) is Message:
            self._telegram.delete_message(message.message_id)

    def __delete_last_user_message(self):
        self.__delete(self.last_user_message)

    # menu keyboard factories

    def __no_keyboard(self) -> ReplyKeyboardRemove:
        return self.__remove_keyboard_command

    def __main_menu_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(self._item_names.get('text_hiding'))
        markup.row(self._item_names.get('reminder_selector'))
        markup.row(self._item_names.get('exit'))
        return markup

    def __reminder_selector_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for name in self._reminders.keys():
            markup.row(KeyboardButton(name))
        markup.row(self._item_names.get('back'))
        markup.row(self._item_names.get('exit'))
        return markup

    def __reminder_settings_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(self._item_names.get('reminder_configure_messages'))
        markup.row(self._item_names.get('reminder_configure_time'))
        markup.row(self._item_names.get('back'))
        markup.row(self._item_names.get('exit'))
        return markup

    def __input_string_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(self._item_names.get('cancel'))
        markup.row(self._item_names.get('exit'))
        return markup

    def __input_bool_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(self._item_names.get('True'), self._item_names.get('False'))
        markup.row(self._item_names.get('cancel'))
        markup.row(self._item_names.get('exit'))
        return markup

    # navigation

    def _show_menu(self, menu_page_name: str):
        self.__delete_last_user_message()
        self._active_menu_page = menu_page_name
        self._menu_page_message_senders[menu_page_name]()

    # main message handler

    def __generic_message_handler(self, message: Message):
        self.last_user_message = message
        if self.last_user_message.text == self._item_names.get('settings_command'):
            self._show_menu('main')
        elif self.last_user_message.text == self._item_names.get('exit'):
            self._show_menu('none')
        else:
            self._menu_handlers[self._active_menu_page](self.last_user_message)

    # menu actions handlers
    def __no_menu_input_handler(self, __: Message) -> None:
        self.__send("Некорректный ввод. Для входа в настройки отправь /settings")

    def __main_menu_input_handler(self, message: Message) -> None:
        if message.text == self._item_names.get('text_hiding'):
            self._show_menu('text_hiding')
        elif message.text == self._item_names.get('reminder_selector'):
            self._show_menu('reminder_selector')
        else:
            self.__send(self._item_names.get('incorrect_input'))

    def __text_hiding_input_handler(self, message: Message) -> None:
        if message.text == self._item_names.get('cancel'):
            self._show_menu('main')
        elif message.text == self._item_names.get('True'):
            self._telegram.hide_text = True
            self._show_menu('main')
        elif message.text == self._item_names.get('False'):
            self._telegram.hide_text = False
            self._show_menu('main')
        else:
            self.__send(self._item_names.get('incorrect_input'))

    def __reminder_selector_input_handler(self, message: Message) -> None:
        if message.text == self._item_names.get('back'):
            self._show_menu('main')
        elif type(self._reminders.get(message.text)) is Reminder:
            self._chosen_reminder = self._reminders.get(message.text)
            self._show_menu('reminder_settings')
        else:
            self.__send(self._item_names.get('incorrect_input'))

    def __reminder_settings_input_handler(self, message: Message) -> None:
        if message.text == self._item_names.get('reminder_configure_messages'):
            self._show_menu('reminder_messages_settings')
        elif message.text == self._item_names.get('reminder_configure_time'):
            self._show_menu('reminder_time_settings')
        elif message.text == self._item_names.get('back'):
            self._show_menu('reminder_selector')
        else:
            self.__send(self._item_names.get('incorrect_input'))

    def __reminder_messages_settings_input_handler(self, message: Message) -> None:
        if message.text == self._item_names.get('cancel'):
            self._show_menu('reminder_settings')
            return

        messages: list[str] = message.text.split(';')
        messages = list(filter(lambda current: type(current) is str and len(current) > 0, messages))
        if len(messages) == 0:
            self.__send("Некорректный ввод. Отправь новый список напоминаний или нажми 'Отмена'")
            return
        self._chosen_reminder.messages = messages
        self._show_menu('reminder_settings')

    def __reminder_time_settings_input_handler(self, message: Message) -> None:
        if message.text == self._item_names.get('cancel'):
            self._show_menu('reminder_settings')
            return

        numbers: list[str] = message.text.split(' ')
        numbers = list(filter(lambda current: type(current) == str and current.isnumeric(), numbers))
        if not len(numbers) == 2:
            self.__send("Некорректный ввод. Отправь новый интервал или нажми 'Отмена'")
            return

        min_time = int(numbers[0])
        max_time = int(numbers[1])
        if min_time > max_time:
            self.__send("Некорректный ввод. min_time должно быть меньше чем max_time.\n"
                        "Отправь новый интервал или нажми 'Отмена'")
            return
        if min_time <= 0 or max_time <= 0:
            self.__send("Некорректный ввод. min_time и max_time должны быть больше 0.\n"
                        "Отправь новый интервал или нажми 'назад' для отмены")
            return

        self._chosen_reminder.wait_time_range = (min_time, max_time)
        self._show_menu('reminder_settings')

    # menu description text senders

    def __send_menu_exit_text(self):
        self.__send('Выход из настроек. Для того чтобы снова открыть это меню, отправь /settings')

    def __send_main_menu_text(self):
        self.__send(f'Настройки')

    def __send_toggle_message_hiding_text(self):
        current_state_string: str = self._item_names.get(str(self._telegram.hide_text)).lower()
        self.__send(f'Скрывать текст сообщений? Текущее состояние: {current_state_string}')

    def __send_reminder_selector_text(self):
        self.__send(f'Выбери профиль напоминаний для настройки')

    def __send_reminder_settings_text(self):
        min_minutes, max_minutes = self._chosen_reminder.wait_time_range
        self.__send(f'Настраиваем профиль {self._chosen_reminder.name}.\n'
                    f'Список напоминаний: {self._chosen_reminder.messages}\n'
                    f'Временной интервал между напоминаниями:\n'
                    f'От {timedelta(minutes=min_minutes)} до {timedelta(minutes=max_minutes)}\n'
                    f'Выбери настройку из списка:')

    def __send_reminder_configure_messages_text(self):
        current_messages_string = reduce(lambda a, b: f'{a};{b}', self._chosen_reminder.messages)
        self.__send(f'Настраиваем список напоминаний в профиле {self._chosen_reminder.name}.\n'
                    f'Отправь новый список сообщений, разделенных точкой с запятой, без пробелов между напоминаниями.\n'
                    f'В списке должно быть как минимум одно напоминание.\n'
                    f'Текущий список:\n'
                    f'{current_messages_string}')

    def __send_reminder_configure_time_text(self):
        min_time, max_time = self._chosen_reminder.wait_time_range
        self.__send(f'Настраиваем временной интервал между напоминаниями в профиле {self._chosen_reminder.name}.\n'
                    f'Отправь новый интервал в минутах, два числа разделенных пробелом.\n'
                    f'Формат: \"min_time max_time\".\n'
                    f'Текущее значение: {min_time} {max_time}')

    # accessors

    @property
    def last_bot_message(self) -> Message:
        return self.__last_bot_message

    @last_bot_message.setter
    def last_bot_message(self, new_message: Message) -> None:
        self.__delete(self.__last_bot_message)
        self.__last_bot_message = new_message

    @property
    def last_user_message(self) -> Message:
        return self.__last_user_message

    @last_user_message.setter
    def last_user_message(self, new_message: Message) -> None:
        self.__delete(self.__last_user_message)
        self.__last_user_message = new_message
