import logging

loggers_list = dict()


class Logger:
    level = logging.INFO
    filename = 'py_log.log'
    filemode = 'w'
    log_format = '%(asctime)s - [%(levelname)s] -  %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'

    @classmethod
    def _file_handler(cls):
        file_handler = logging.FileHandler(cls.filename, mode=cls.filemode, encoding='utf-8')
        file_handler.setLevel(cls.level)
        file_handler.setFormatter(logging.Formatter(cls.log_format))
        return file_handler

    @classmethod
    def _stream_handler(cls):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(cls.level)
        stream_handler.setFormatter(logging.Formatter(cls.log_format))
        return stream_handler

    @classmethod
    def get(cls, module):
        if module in loggers_list.keys():
            return loggers_list[module]

        logger = logging.getLogger(module)
        logger.setLevel(cls.level)
        logger.addHandler(cls._file_handler())
        logger.addHandler(cls._stream_handler())
        loggers_list.update({module: logger})
        return logger


