import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.readConfig import ReadConfig

from playwright.sync_api import Page

# 登录相关常量
PASSWORD_XPATH = "//*[@id='password']"

def _get_password() -> str:
    """从 config.ini 读取登录密码，读取失败时返回默认值。"""
    try:
        config = ReadConfig()
        return config.read_config('login', 'password')
    except Exception:
        return "111111"

DEFAULT_PASSWORD = _get_password()


def login_fill_password(page: Page, password: str = DEFAULT_PASSWORD):
    """在登录页填入密码并尝试提交表单。

    策略：优先使用 xpath 填入密码并按回车；若存在提交按钮则点击，
    最后等待导航完成（取代硬编码 sleep）。
    """
    try:
        sel = f"xpath={PASSWORD_XPATH}"
        pwd_loc = page.locator(sel)
        pwd_loc.wait_for(state="visible", timeout=10000)
        try:
            page.fill(sel, password)
        except Exception:
            # fallback: 通过 JS 设置 value
            page.evaluate(
                "(p, v) => { const el = document.evaluate(p, document, null, "
                "XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue; "
                "if (el) el.value = v; }",
                PASSWORD_XPATH, password,
            )

        # 提交表单
        try:
            pwd_loc.press("Enter")
        except Exception:
            try:
                page.click("button[type=submit]")
            except Exception:
                try:
                    page.click("button:has-text('登录')")
                except Exception:
                    page.keyboard.press("Enter")

        # 等待页面稳定（使用 domcontentloaded 而非 networkidle，SPA 长轮询不会触发 networkidle）
        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            # 额外等待关键元素出现，确认登录后的页面已渲染
            page.wait_for_selector("body", state="visible", timeout=5000)
        except Exception:
            pass  # 超时不阻塞，后续测试中的 wait_for 会兜底
    except Exception:
        raise


def login_fn(page: Page):
    """示例登录函数：只填写密码并提交。若需要填写用户名或其他字段，请扩展此函数。"""
    login_fill_password(page, DEFAULT_PASSWORD)
