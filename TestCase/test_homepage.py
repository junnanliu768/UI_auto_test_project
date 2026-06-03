import os
from datetime import datetime
import sys
# 将项目根目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from common.baseDriver import BaseDriver
from common.auth import login_fn
from common.pages.home_page import HomePage


def _save_screenshot(page, name: str):
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "screenshots")
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"{name}_{ts}.png")
    try:
        page.screenshot(path=path, full_page=True)
    except Exception:
        # 忽略截图异常，不影响测试框架的断言传播
        pass


@pytest.fixture(scope="module")
def driver_page():
    """模块级 fixture：启动浏览器、执行登录检查并在模块结束时关闭浏览器。

    这样在同一个测试文件中只登录一次，后续测试共享同一个浏览器页面。
    """
    driver = BaseDriver()
    page = driver.start_browser()
    try:
        try:
            login_fn(page)
        except Exception:
            # 登录异常不应阻止 fixture 创建，由测试里处理失败信息
            pass
        yield driver, page
    finally:
        driver.close_browser()


def test_robot_status_is_active(request, driver_page):
    driver, page = driver_page
    home = HomePage(page)
    status = home.get_status()
    try:
        assert status.lower() == "active", f"期望状态为 'ACTIVE'，实际: {status}"
    except AssertionError:
        _save_screenshot(page, request.node.name + "_status")
        raise


def test_robot_model_is_m7(request, driver_page):
    driver, page = driver_page
    home = HomePage(page)
    model = home.get_model()
    try:
        assert model == "M7", f"期望型号为 'M7'，实际: {model}"
    except AssertionError:
        _save_screenshot(page, request.node.name + "_model")
        raise


def test_robot_hand_is_none(request, driver_page):
    driver, page = driver_page
    home = HomePage(page)
    hand = home.get_hand()
    try:
        assert hand == "无", f"期望灵巧手为 '无'，实际: {hand}"
    except AssertionError:
        _save_screenshot(page, request.node.name + "_hand")
        raise

