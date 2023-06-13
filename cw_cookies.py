import requests
import configparser
import pickle
from bs4 import BeautifulSoup


def check_cookies(session: requests.Session) -> bool:
    """
    Проверка работоспособности куки

    :param session: сессия с установленными куки
    :return: 1 в случае успеха, иначе 0
    """
    html = session.get('https://catwar.su/').text
    soup = BeautifulSoup(html, 'html.parser')
    if soup.find('a', href='loadAvatar') is None:
        return 0
    return 1


def upd_cookies(session, logger):
    """
    Обновление куки в файле

    :param session: сессия без куки
    :param logger: логгер класса Bot
    """
    config = configparser.ConfigParser()
    config.read("config.ini", encoding="utf-8")
    config = config["CATWAR"]
    data = {'mail': config['mail'], 'pass': config['password']}
    try:
        data.update({'cat': config['cat']})
    except KeyError:
        pass
    session.post('https://catwar.su/ajax/login', data)
    with open('cookies.txt', 'wb') as f:
        pickle.dump(session.cookies, f)
    logger.warning("Куки записаны в файл. Плановая перезагрузка...")
    exit(0)


def get_cookies(logger) -> requests.Session:
    """
    Загрузка куки, либо их получение при необходимости

    :param logger: логгер класса Bot
    :return: сессия с установленными куки
    """
    session = requests.session()
    user_agent_val = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                     'Chrome/90.0.4430.93 Safari/537.36 '
    session.headers.update({'User-Agent': user_agent_val})

    try:
        f = open('cookies.txt', 'rb')
    except IOError or FileNotFoundError:
        logger.warning("Не удалось загрузить куки. Попытка получения...")
        upd_cookies(session, logger)
    else:
        with f:
            session.cookies.update(pickle.load(f))
        if check_cookies(session):
            return session
        else:
            logger.warning("Не получается авторизоваться с текущими куки")
            raise Exception("Invalid cookies")
