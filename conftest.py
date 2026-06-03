import os
import glob

import pytest
import allure


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # This hook yields the test report object which we can modify.
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        # 查找对应的截图文件（根据 test 名称前缀）
        screenshot_dir = os.path.join(str(item.config.rootdir), "reports", "screenshots")
        pattern = os.path.join(screenshot_dir, f"{item.name}_*.png")
        files = glob.glob(pattern)
        if files:
            latest = max(files, key=os.path.getctime)
            try:
                allure.attach.file(latest, name=os.path.basename(latest), attachment_type=allure.attachment_type.PNG)
            except Exception:
                # 如果附件失败，不阻塞测试流程
                pass
