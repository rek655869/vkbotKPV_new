import requests
import configparser
import pickle
import os

def upd_cookies():
    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__))
          + "/config.ini", encoding="utf-8")
    config = config["CATWAR"]
    s = requests.session()
    user_agent_val = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                     'Chrome/90.0.4430.93 Safari/537.36 '
    s.headers.update({'User-Agent': user_agent_val})
    data = {'mail': config['mail'], 'pass': config['password']}
    try:
        data.update({'cat': config['cat']})
    except KeyError:
        pass
    s.post('https://catwar.su/ajax/login', data)
    with open('cookies.txt', 'wb') as f:
        pickle.dump(s.cookies, f)


def get_cookies():
    s = requests.session()
    user_agent_val = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                     'Chrome/90.0.4430.93 Safari/537.36 '
    s.headers.update({'User-Agent': user_agent_val})
    try:
        f = open(os.path.dirname(os.path.abspath(__file__))
          + '/cookies.txt', 'rb')
    except IOError or FileNotFoundError:
        upd_cookies()
        get_cookies()
    else:
        with f:
            s.cookies.update(pickle.load(f))
        return s


if __name__ == '__main__':
    upd_cookies()
