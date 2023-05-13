from logger import Logger
import threading
import schedule
from datetime import datetime, timedelta
import time


class Deliveryman:
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger.get(__name__)
        threading.Thread(target=self._start, name='mailing', daemon=False).start()


    def _start(self):
        self.logger.info("Deliveryman запущен")
        schedule.every().minute.at(":00").do(self.check_reminders)
        while True:
            schedule.run_pending()
            time.sleep(10)


    def check_reminders(self):
        current_time = datetime.now()
        self.logger.info(current_time)
        after_5 = current_time + timedelta(minutes=5)
        after_10 = current_time + timedelta(minutes=10)
        actions_after_5 = self._get_actions(after_5.strftime("%H:%M"), 5)
        actions_after_10 = self._get_actions(after_10.strftime("%H:%M"), 10)
        self.logger.info(actions_after_5)
        self.logger.info(actions_after_10)

        for user_id, action in actions_after_5:
            self.bot.vk.send(user_id, f"Через 5 минут будет {action}!")
            time.sleep(0.05)
        for user_id, action in actions_after_10:
            self.bot.vk.send(user_id, f"Через 10 минут будет {action}!")
            time.sleep(0.05)
        time.sleep(1)


    def _get_actions(self, current_time, time):
        sql = 'SELECT reminders.vk_id, actions.name FROM actions ' \
              'INNER JOIN reminders ON actions.id = reminders.action_id WHERE actions.time = "{}" AND reminders.remind_time={}'\
            .format(current_time, time)
        return self.bot.db.fetchall(sql)
