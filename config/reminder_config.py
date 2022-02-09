from typing import Callable, Any


class ReminderConfig:
    _name: str
    _messages: list[str]
    _time_range: tuple[int, int]
    _dump: Callable[[None], None]

    def __init__(self,
                 name: str,
                 messages: list[str],
                 time_range: tuple[int, int],
                 dump_callback: Callable[[], None]):
        self._name = name
        self._messages = messages
        self._time_range = time_range
        self._dump = dump_callback

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name
        self._dump()

    @property
    def messages(self) -> list[str]:
        return self._messages

    @messages.setter
    def messages(self, new_messages: list[str]) -> None:
        self._messages = new_messages
        self._dump()

    @property
    def time_range(self) -> tuple[int, int]:
        return self._time_range

    @time_range.setter
    def time_range(self, new_range: tuple[int, int]) -> None:
        self._time_range = new_range
        self._dump()

    def to_dict(self) -> dict[str, Any]:
        return {
            '_name': self._name,
            '_messages': self._messages,
            '_time_range': self._time_range
        }
