from logger import Logger
import threading
import schedule
from datetime import datetime, timedelta
import time


class Deliveryman:
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger.get(__name__)
        threading.Thread(target=self._start, name='mailing', daemon=True).start()


    def _start(self):
        self.logger.info("Deliveryman запущен")
        schedule.every(1).minutes.do(self.check_reminders)
        while True:
            schedule.run_pending()
            time.sleep(1)


    def check_reminders(self):
        current_time = datetime.now()
        after_5 = current_time + timedelta(minutes=5)
        after_10 = current_time + timedelta(minutes=10)
        actions_after_5 = self._get_actions(after_5.strftime("%H:%M"))
        actions_after_10 = self._get_actions(after_10.strftime("%H:%M"))

        for user_id, action in actions_after_5:
            self.bot.vk.send(user_id, f"Через 5 минут будет {action}!")
            time.sleep(0.05)
        for user_id, action in actions_after_10:
            self.bot.vk.send(user_id, f"Через 10 минут будет {action}!")
            time.sleep(0.05)



    def _get_actions(self, current_time):
        sql = 'SELECT reminders.vk_id, actions.name FROM actions ' \
              'INNER JOIN reminders ON actions.id = reminders.action_id WHERE actions.time = "{}"'\
            .format(current_time)
        return self.bot.db.fetchall(sql)
