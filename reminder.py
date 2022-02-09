from datetime import timedelta
from threading import Thread
from time import sleep
from typing import Generator, Tuple, Callable

from requests import get
from telebot.types import Message

from config.reminder_config import ReminderConfig


class Reminder(Thread):
    _config: ReminderConfig
    # function to send message. args: message, hide_text, keyboard_markup
    _send_message_callback: Callable[[str], Message]
    _wait_time_generator: Generator[int, None, None]
    _message_index_generator: Generator[int, None, None]

    def __init__(self,
                 config: ReminderConfig,
                 send_message_callback: Callable[[str], Message]):
        super().__init__()
        self._config = config
        self._send_message_callback = send_message_callback

        # Using setters to init random generators
        self.messages = config.messages
        self.wait_time_range = config.time_range

    def run(self) -> None:
        while True:
            self._await_for_timeout()
            self._send_message()

    def _send_message(self):
        message_index = next(self._message_index_generator)
        self._send_message_callback(self.messages[message_index])

    def _await_for_timeout(self) -> None:
        interval = next(self._wait_time_generator) * 60
        next_send_message = f'{self.name}: next after {timedelta(seconds=interval)}'
        print(next_send_message)
        sleep(interval)

    def __random_generator(self, min_value: int, max_value: int, batch_size: int = 50) -> Generator[int, None, None]:
        while True:
            numbers = self.__get_randoms_batch(min_value, max_value, batch_size)
            for number in numbers:
                yield number

    @staticmethod
    def __zeros_generator() -> Generator[int, None, None]:
        while True:
            yield 0

    @staticmethod
    def __get_randoms_batch(min_number: int, max_number: int, numbers_count: int = 1) -> list:
        response = get(f'https://www.random.org/integers/?'
                       f'num={numbers_count}&'
                       f'min={min_number}&'
                       f'max={max_number}&'
                       f'col=1&'
                       f'base=10&'
                       f'format=plain&'
                       f'rnd=new')
        result = filter(lambda item: len(item) > 0, response.text.split('\n'))
        result = map(lambda item: int(item), result)
        return list(result)

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def messages(self) -> list[str]:
        return self._config.messages

    @messages.setter
    def messages(self, new_messages: list[str]) -> None:
        if not self._config.messages == new_messages:
            self._config.messages = new_messages

        if len(new_messages) > 1:
            self._message_index_generator = self.__random_generator(0, len(new_messages) - 1)
        else:
            self._message_index_generator = self.__zeros_generator()
        print(f'Reminder \'{self.name}\' messages updated: {new_messages}')

    @property
    def wait_time_range(self) -> Tuple[int, int]:
        return self._config.time_range

    @wait_time_range.setter
    def wait_time_range(self, new_range: Tuple[int, int]) -> None:
        if not self._config.time_range == new_range:
            self._config.time_range = new_range

        self._wait_time_generator = self.__random_generator(*new_range)
        print(f'Reminder \'{self.name}\' time range updated: {new_range}')
