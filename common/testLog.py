'''
coding: utf-8
Time: Do not edit
Author: ljn
File: Do not edit
Description: 
'''




import colorlog
import logging.config

# 定义彩色日志格式
LOG_COLORS = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

LOGGING_DIC = {
    'version': 1.0,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '"日志:%(name)s-级别:%(levelname)s-时间:%(asctime)s-模块:%(module)s.py-第%(lineno)d行:%(message)s"',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s日志:%(name)s-级别:%(levelname)s-时间:%(asctime)s-模块:%(module)s.py-第%(lineno)d行:%(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'log_colors': LOG_COLORS,
        },
    },
    'handlers': {
        'console_debug_handler': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
    },
    'loggers': {
        'debug_log': {
            'handlers': ['console_debug_handler'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}


def log():
    logging.config.dictConfig(LOGGING_DIC)
    logger = logging.getLogger('debug_log')
    return logger


logger = log()

if __name__ == '__main__':
    logger.debug("这是一条 DEBUG 级别的日志")
    logger.info("这是一条 INFO 级别的日志（绿色）")
    logger.warning("这是一条 WARNING 级别的日志（黄色）")
    logger.error("这是一条 ERROR 级别的日志（红色）")
    logger.critical("这是一条 CRITICAL 级别的日志（加粗红色）")
