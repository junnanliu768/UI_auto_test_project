from playwright.sync_api import Page


class HomePage:
    """页面对象：首页（Home）

    定位策略：使用“字段标签”作为锚点（例如页面中显示的中文标签：'状态'、'型号'、'灵巧手'），
    然后从包含该标签的容器中提取实际显示值（通常是容器文本的后续行）。

    说明：相比直接使用固定文本或复杂 XPath，这种方法在前端只要保持标签存在即可更稳健。
    若前端可配合，请优先提供 `data-test-id` 或 `id` 等稳定属性，我们可以直接使用它们。
    """

    # 标签文本（可根据页面语言或变化修改）
    STATUS_LABEL = "状态"
    MODEL_LABEL = "型号"
    HAND_LABEL = "灵巧手"

    # XPath 模板：用标签文本定位对应的值元素
    XPATH_TEMPLATES = [
        # 模式1: 标签和值在同一行（flex），值是紧跟标签之后的兄弟 div
        "//div[normalize-space()='{label}']/following-sibling::div[1]",
        # 模式2: 包含标签的父容器中，取除标签外的 p/h3/span
        "//*[contains(text(),'{label}')]/parent::div//p[not(contains(text(),'{label}'))]",
        "//*[contains(text(),'{label}')]/parent::div//h3[not(contains(text(),'{label}'))]",
        "//*[contains(text(),'{label}')]/parent::div//span[not(contains(text(),'{label}'))]",
        # 模式3: 包含标签文本的 div 自身
        "//*[contains(text(),'{label}')]/parent::div",
    ]

    def __init__(self, page: Page):
        self.page = page

    def get_status(self) -> str:
        """返回机器人状态文本，例如 'ACTIVE'"""
        return self._get_text_by_label(self.STATUS_LABEL)

    def get_model(self) -> str:
        """返回机器人型号文本，例如 'M7'"""
        return self._get_text_by_label(self.MODEL_LABEL)

    def get_hand(self) -> str:
        """返回灵巧手显示文本，例如 '无'"""
        return self._get_text_by_label(self.HAND_LABEL)

    def _get_text_by_label(self, label: str) -> str:
        """通过标签文本精确定位对应值。

        策略：按模板顺序尝试 XPath，找到非空且不等于标签本身的文本即返回。
        """
        for xp in self.XPATH_TEMPLATES:
            xpath_expr = xp.replace("{label}", label)
            try:
                loc = self.page.locator(f"xpath={xpath_expr}")
                count = loc.count()
                if count == 0:
                    continue
                for i in range(min(count, 3)):
                    try:
                        el = loc.nth(i)
                        el.wait_for(state="visible", timeout=3000)
                        text = el.inner_text().strip()
                        if text and text != label:
                            # 文本若含多行（如"状态\nACTIVE"），取非标签行
                            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                            for idx, ln in enumerate(lines):
                                if ln == label and idx + 1 < len(lines):
                                    return lines[idx + 1]
                            return text
                    except Exception:
                        continue
            except Exception:
                continue

        # 兜底：文本拆分
        try:
            container = self.page.locator(f"div:has-text('{label}')").first
            container.wait_for(state="visible", timeout=5000)
            full = container.inner_text()
            lines = [ln.strip() for ln in full.splitlines() if ln.strip()]
            for idx, ln in enumerate(lines):
                if ln == label and idx + 1 < len(lines):
                    return lines[idx + 1]
        except Exception:
            pass
        return ""
