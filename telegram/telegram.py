from typing import Optional

from telebot import TeleBot
from telebot.types import MessageEntity, ReplyKeyboardMarkup, Message
from config import Config


class Telegram:
    bot: TeleBot
    _config: Config

    def __init__(self):
        self._config = Config()
        self.bot = TeleBot(self._tg_key, threaded=False)

    # messages

    def send(self,
             message: str,
             hide_text: Optional[bool] = None,
             keyboard_markup: Optional[ReplyKeyboardMarkup] = None) -> Message:
        entities: Optional[list[MessageEntity]] = None
        if hide_text is None:
            hide_text = self.hide_text
        if hide_text:
            entities = [MessageEntity('spoiler', 0, len(message))]
        return self._send(message, entities=entities, keyboard_markup=keyboard_markup)

    def _send(self,
              message: str,
              entities: Optional[list[MessageEntity]] = None,
              keyboard_markup: Optional[ReplyKeyboardMarkup] = None
              ) -> Message:
        return self.bot.send_message(self.chat_id, message, entities=entities, reply_markup=keyboard_markup)

    def delete_message(self, message_id: int) -> None:
        self.bot.delete_message(self.chat_id, message_id)

    # getters

    @property
    def _tg_key(self) -> str:
        return self._config.tg_key

    @property
    def chat_id(self) -> int:
        return self._config.tg_chat_id

    @property
    def hide_text(self) -> bool:
        return self._config.tg_hide_text

    @hide_text.setter
    def hide_text(self, value: bool) -> None:
        self._config.tg_hide_text = value
