
import sys
import os
# 将项目根目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 然后导入需要的模块
from common.baseDriver import BaseDriver
from common.readConfig import ReadConfig
from common.testLog import logger
import time




if __name__ == '__main__':
    logger.info("执行成功")
    driver = BaseDriver() 
    url = ReadConfig().get_url()
    logger.info(f"从配置文件获取到的 URL: {url}")
    page = driver.start_browser()
    page.goto(url)
    driver.maximize_window()
    time.sleep(20)
    driver.close_browser()