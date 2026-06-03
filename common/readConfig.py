
import os
import sys
# 兼容直接运行和包导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.testLog import logger
from configparser import ConfigParser, NoSectionError, NoOptionError

class ReadConfig:
    def __init__(self):
        # 获取项目根目录下的 config.ini
        self.path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.ini')
        self.conf = ConfigParser()
        logger.info(f"配置文件路径: {self.path}")

    def read_config(self, *args):
        # 缓存：文件未变更时不重复读取
        if not self.conf.sections():
            self.conf.read(self.path, encoding='utf-8')
        try:
            if len(args) == 0:
                sections = self.conf.sections()
                logger.info(f"获取所有sections: {sections}")
                return sections
            elif len(args) == 1:
                section = args[0]
                if not self.conf.has_section(section):
                    logger.error(f"Section '{section}' 不存在")
                    raise NoSectionError(section)
                items = dict(self.conf.items(section))
                logger.info(f"获取section '{section}' 的所有配置项: {items}")
                return items
            elif len(args) == 2:
                section, option = args
                if not self.conf.has_section(section):
                    logger.error(f"Section '{section}' 不存在")
                    raise NoSectionError(section)
                if not self.conf.has_option(section, option):
                    logger.error(f"Option '{option}' 不存在于 section '{section}'")
                    raise NoOptionError(option, section)
                value = self.conf.get(section, option)
                logger.info(f"获取配置值 '{section}.{option}': {value}")
                return value
            else:
                logger.error("参数数量不正确，最多接受2个参数")
                raise ValueError("参数数量不正确，最多接受2个参数")
        except Exception as e:
            logger.error(f"读取配置发生异常: {e}")
            raise

    def get_url(self):
        # 直接获取 driverUrl 下的 url
        return self.read_config('driverUrl', 'url')

if __name__ == '__main__':
    rd = ReadConfig()
    # 打印 config.ini 内容，便于调试
    with open(rd.path, encoding='utf-8') as f:
        logger.info("config.ini 内容:\n" + f.read())
    try:
        url = rd.get_url()
        logger.info(f"获取到的 url: {url}")
    except Exception as e:
        logger.error(f"配置读取失败: {e}")