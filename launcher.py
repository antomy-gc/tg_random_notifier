from reminder import Reminder
from telegram import BotMenuThread, Telegram
from config import Config


config = Config()
telegram = Telegram()

reminders: dict[str, Reminder] = dict()
for reminder_name, reminder_config in config.reminders.items():
    reminders[reminder_name] = Reminder(reminder_config, telegram.send)

telegram_menu = BotMenuThread(telegram, reminders)
telegram_menu.start()

for thread in reminders.values():
    thread.start()
