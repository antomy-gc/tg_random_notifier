import json
from typing import Callable, Any

from .reminder_config import ReminderConfig


class Config:
    _tg_key: str
    _tg_chat_id: int
    _tg_hide_text: bool
    _reminders: dict[str, ReminderConfig]

    def __init__(self):
        with open('config.json', 'r', encoding='utf8') as json_file:
            loaded_data = json.load(json_file)
            self._tg_key = loaded_data['_tg_key']
            self._tg_chat_id = loaded_data['_tg_chat_id']
            self._tg_hide_text = loaded_data['_tg_hide_text']
            self._reminders = Config._load_reminder_configs(loaded_data['_reminders'], self._dump)
            print("Config loaded from file")

    @property
    def tg_key(self) -> str:
        return self._tg_key

    @tg_key.setter
    def tg_key(self, value: str) -> None:
        self._tg_key = value
        self._dump()

    @property
    def tg_chat_id(self) -> int:
        return self._tg_chat_id

    @tg_chat_id.setter
    def tg_chat_id(self, value: int) -> None:
        self._tg_chat_id = value
        self._dump()

    @property
    def tg_hide_text(self) -> bool:
        return self._tg_hide_text

    @tg_hide_text.setter
    def tg_hide_text(self, value: bool) -> None:
        self._tg_hide_text = value
        self._dump()

    @property
    def reminders(self) -> dict[str, ReminderConfig]:
        return self._reminders

    def _dump(self) -> None:
        reminders_serialized: list[dict[str, Any]] = list(
            map(lambda reminder_config: reminder_config.to_dict(), self._reminders.values()))

        config_dict = {
            '_tg_key': self._tg_key,
            '_tg_chat_id': self._tg_chat_id,
            '_tg_hide_text': self._tg_hide_text,
            '_reminders': reminders_serialized
        }

        with open('config.json', 'w', encoding='utf8') as json_file:
            json.dump(config_dict, json_file, ensure_ascii=False, indent=4)
            print("Config changes saved to file")

    @staticmethod
    def _load_reminder_configs(reminders_serialized: list[dict[str, Any]],
                               dump_callback: Callable[[], None]) -> dict[str, ReminderConfig]:
        result: dict[str, ReminderConfig] = dict()
        for reminder in reminders_serialized:
            config_name = reminder.get('_name')
            config_messages = reminder.get('_messages')
            time_range_list: list[int] = reminder.get('_time_range')
            config_time_range = (time_range_list[0], time_range_list[1])
            result[config_name] = ReminderConfig(config_name, config_messages, config_time_range, dump_callback)
        return result

