from logger import Logger
import threading
import schedule
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


def get_key(d, value):
    for k, v in d.items():
        for x in v:
            if x == value:
                return k


class Updater:
    def __init__(self, bot):
        self.bot = bot
        self.logger = Logger.get(__name__)
        threading.Thread(target=self._start, name='updater', daemon=False).start()

        self.pages_info = {
            'верх': {
                'start': 'верх!',
                'end': 'конец верх',
                'page_ids': [],
            },
            'старейшины': {
                'start': 'стар!',
                'end': 'конец стар',
                'page_ids': [],
            },
            'избранники': {
                'start': 'избранники!',
                'end': 'конец избранники',
                'page_ids': [],
            },
            'стражи': {
                'start': 'стражи!',
                'end': 'конец стражи',
                'page_ids': [56444151],
            },
            'охотники': {
                'start': 'стражи!',
                'end': 'конец стражи',
                'page_ids': [],
            },
            'будущие стражи': {
                'start': 'стражи!',
                'end': 'конец стражи',
                'page_ids': [],
            },
            'прочие': {
                'start': 'прочие!',
                'end': 'прочие верх',
                'page_ids': [56445286],
            },
        }
        self.positions = {
            ('врачеватель', 'врачевательница'): [],
            ('ученик врачевателя', 'ученица врачевателя'): [],
            ('советник', 'советница'): [],
            ('доверенный', 'доверенная'): [],
            ('избранник ласки',): [],
            ('избранник иволги',): [],
            ('избранник лисы',): [],
            ('страж', 'стражница'): [],
            ('охотник', 'охотница'): [],
            ('будущий страж', 'будущая стражница'): [],
            ('будущий охотник', 'будущая охотница'): [],
            ('котёнок',): [],
            ('старейшина',): [],
            ('переходящий', 'переходящая'): [],
            ('разрешение',): [],
        }

        self.ivolga = '<img border="0" src="http://images.vfl.ru/ii/1604159092/1dda3f82/32141463.png"/>)'
        self.lisa = '<img border="0" src="http://images.vfl.ru/ii/1604159092/448b5ed6/32141465.png"/>'
        self.laska = '<img border="0" src="http://images.vfl.ru/ii/1604159092/ed9c5fbd/32141464.png"/>'

    def _start(self):
        self.logger.info("Updater запущен")
        schedule.every().day.at("03:00").do(self.check_to_del)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def check_to_del(self):
        self.logger.info("Начата проверка пользователей...")
        users = self._get_wait_users()
        for user_id, timestamp in users:
            last_time = datetime.fromtimestamp(timestamp)
            time_after_3 = last_time + timedelta(days=3)
            if datetime.now() - timedelta(minutes=30) < time_after_3 < datetime.now() + timedelta(minutes=30):
                self.del_user(user_id)
        self.check_users()

    def check_users(self):
        users_with_perm = self._get_perm()
        for user_id, cw_id, _ in self.bot.db.get_users():
            html = self.bot.cw.get(f'https://catwar.su/cat{cw_id}').text
            soup = BeautifulSoup(html, 'html.parser')
            profile = soup.find(attrs={"data-cat": cw_id})
            try:
                position = profile.find('i').text.lower()
                name = profile.find('big').text
            except AttributeError:
                if cw_id in users_with_perm:
                    position = 'разрешение'
                    try:
                        name = profile.find('big').text
                    except AttributeError:
                        name = ""
                else:
                    self.to_wait_user(user_id)
                    continue
            vk_name = self.bot.vk.admin.users.get(user_ids=user_id, fields='first_name, last_name')[0]
            vk_name = vk_name['first_name'] + ' ' + vk_name['last_name']

            for key, item in self.positions.items():
                text = f'|-\n| [[id{user_id}|{vk_name}]]\n| [{name}|{cw_id}]\n| [https://catwar.su/cat{cw_id}]\n'

                if position == 'избранник духов' or position == 'избранница духов':
                    for img in profile.find_all(border='0'):
                        if str(img) == self.ivolga:
                            self.positions[('избранник иволги',)].append(text)
                            break
                        elif str(img) == self.laska:
                            self.positions[('избранник ласки',)].append(text)
                            break
                        elif str(img) == self.lisa:
                            self.positions[('избранник лисы',)].append(text)
                            break

                elif position in key:
                    self.positions.get(key).append(text)

        self.update_pages()

    def update_pages(self):
        self.logger.info("Начато обновление вики-страниц...")
        html = ''
        for page, info in self.pages_info.items():
            if page == 'верх':
                html = info['start'] + "<center>'''Врачеватель'''</center>\n{|\n"
                html += ''.join(self.positions[('врачеватель', 'врачевательница')])
                html += "|}\n<center>'''Ученик врачевателя'''</center>\n{|\n"
                html += ''.join(self.positions[('ученик врачевателя', 'ученица врачевателя')])
                html += "|}\n<center>'''Советники'''</center>\n{|\n"
                html += ''.join(self.positions[('советник', 'советница')])
                html += "|}\n<center>'''Доверенные'''</center>\n{|\n"
                html += ''.join(self.positions[('доверенный', 'доверенная')])
                html += '|}\n' + info['end']

            elif page == 'старейшины':
                html = info['start'] + '{|\n'
                html += ''.join(self.positions[('старейшина',)])
                html += '|}\n' + info['end']

            elif page == 'избранники':
                html = info['start'] + "<center>'''Избранники Иволги'''</center>\n{|\n"
                html += ''.join(self.positions[('избранник иволги',)])
                html += "|}\n<center>'''Избранники Лисы'''</center>\n{|\n"
                html += ''.join(self.positions[('избранник лисы',)])
                html += "|}\n<center>'''Избранники Ласки'''</center>\n{|\n"
                html += ''.join(self.positions[('избранник ласки',)])
                html += '|}\n' + info['end']

            elif page == 'прочие':
                html = info['start'] + "<center>'''Котята'''</center>\n{|\n"
                html += ''.join(self.positions[('котёнок',)])
                html += "|}\n<center>'''Переходящие'''</center>\n{|\n"
                html += ''.join(self.positions[('переходящий', 'переходящая')])
                html += "|}\n<center>'''С разрешением на нахождение в группе'''</center>\n{|\n"
                html += ''.join(self.positions[('разрешение',)])
                html += '|}\n' + info['end']

            elif page == 'стражи':
                users1 = self.positions[('страж', 'стражница')][0:81]
                users2 = self.positions[('страж', 'стражница')][81:len(self.positions[('страж', 'стражница')])+1]
                html = info['start'] + f"\n[[page-{self.bot.vk.group_id}_{info['page_ids'][0]}|1]]" \
                                       f" '''[[page-{self.bot.vk.group_id}_{info['page_ids'][1]}|2]]'''</center>\n"
                html += ''.join(users2)
                html += '|}\n' + f"<center>[[photo350643392_457280594|40x32px;noborder|" \
                                 f"page-{self.bot.vk.group_id}_{info['page_ids'][1]}]]</center>"
                self.bot.vk.save_page(html, info['page_ids'][1])

                html = info['start'] + f"\n'''[[page-{self.bot.vk.group_id}_{info['page_ids'][0]}|1]]'''" \
                                       f" [[page-{self.bot.vk.group_id}_{info['page_ids'][1]}|2]]</center>\n"
                html += ''.join(users1)
                html += '|}\n' + f"<center>[[photo350643392_457280594|40x32px;noborder|" \
                                 f"page-{self.bot.vk.group_id}_{info['page_ids'][0]}]]</center>"

            elif page == 'охотники':
                users1 = self.positions[('охотник', 'охотница')][0:81]
                users2 = self.positions[('охотник', 'охотница')][81:len(self.positions[('охотник', 'охотница')]) + 1]
                html = info['start'] + f"\n[[page-{self.bot.vk.group_id}_{info['page_ids'][0]}|1]]" \
                                       f" '''[[page-{self.bot.vk.group_id}_{info['page_ids'][1]}|2]]'''</center>\n"
                html += ''.join(users2)
                html += '|}\n' + f"<center>[[photo350643392_457280594|40x32px;noborder|" \
                                 f"page-{self.bot.vk.group_id}_{info['page_ids'][1]}]]</center>"
                self.bot.vk.save_page(html, info['page_ids'][1])

                html = info['start'] + f"\n'''[[page-{self.bot.vk.group_id}_{info['page_ids'][0]}|1]]'''" \
                                       f" [[page-{self.bot.vk.group_id}_{info['page_ids'][1]}|2]]</center>\n"
                html += ''.join(users1)
                html += '|}\n' + f"<center>[[photo350643392_457280594|40x32px;noborder|" \
                                 f"page-{self.bot.vk.group_id}_{info['page_ids'][0]}]]</center>"

            elif page == 'будущие':
                users1 = self.positions[('будущий страж', 'будущая стражница')]
                users2 = self.positions[('будущий охотник', 'будущая охотница')]
                html = info['start'] + f"\n[[page-{self.bot.vk.group_id}_{info['page_ids'][0]}|Будущие стражи]]" \
                                       f" | '''[[page-{self.bot.vk.group_id}_{info['page_ids'][1]}|Будущие охотники]]'''</center>"
                html += ''.join(users2)
                html += '|}\n' + f"<center>[[photo350643392_457280594|40x32px;noborder|" \
                                 f"page-{self.bot.vk.group_id}_{info['page_ids'][1]}]]</center>"
                self.bot.vk.save_page(html, info['page_ids'][1])

                html = info['start'] + f"\n'''[[page-{self.bot.vk.group_id}_{info['page_ids'][0]}|Будущие стражи]]'''" \
                                       f" | [[page-{self.bot.vk.group_id}_{info['page_ids'][1]}|Будущие охотники]]</center>"
                html += ''.join(users1)
                html += '|}\n' + f"<center>[[photo350643392_457280594|40x32px;noborder|" \
                                 f"page-{self.bot.vk.group_id}_{info['page_ids'][0]}]]</center>"

            self.bot.vk.save_page(html, info['page_ids'][0])
        self.logger.info("Обновление завершено.")


    def to_wait_user(self, user_id):
        timestamp = datetime.now().timestamp()
        self._add_to_wait(user_id, timestamp)
        self.bot.send(user_id, "Вы покинули клан и будете исключены из группы через 3 дня. Если вы считаете, что это "
                               "ошибка, либо хотите остаться в группе, свяжитесь с представителями верха")


    def del_user(self, user_id):
        self.bot.vk.admin.groups.removeUser(group_id=self.bot.vk.group_id, user_id=user_id)
        sql = 'DELETE FROM users WHERE vk_id={}'.format(user_id)
        self.bot.db.add(sql)

    def _get_wait_users(self):
        sql = 'SELECT * FROM wait_del'
        return self.bot.db.fetchall(sql)

    def _get_perm(self):
        sql = 'SELECT cw_id FROM with_perm'
        res = self.bot.db.fetchall(sql)
        if res:
            return [x[0] for x in res]
        return []

    def _add_to_wait(self, user_id, timestamp):
        sql = 'INSERT INTO wait_del (vk_id, timestamp) VALUES ({}, {})'.format(user_id, timestamp)
        self.bot.db.add(sql)
