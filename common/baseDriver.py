# common/baseDriver.py
import time
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from typing import Optional, Dict, Any, Literal, Callable
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.readConfig import ReadConfig
from common.testLog import logger


class BaseDriver:
    """Playwright 浏览器驱动管理类"""
    
    def __init__(self, url: Optional[str] = None, config_section: str = 'driverUrl', config_key: str = 'url'):
        """初始化驱动
        
        Args:2
            url: 直接指定URL（优先级最高）
            config_section: 配置文件中的section名称
            config_key: 配置文件中的key名称
        """
        # 优先使用参数传入的URL，否则读取配置文件
        if url:
            self.url = url
            logger.info(f"使用传入的URL: {self.url}")
        else:
            try:
                config = ReadConfig()
                self.url = config.read_config(config_section, config_key)
                logger.info(f"从配置文件读取URL: {self.url}")
            except Exception as e:
                # 兜底默认地址
                self.url = "http://192.168.8.100:1888/auth/login"
                logger.warning(f"读取配置失败，使用默认地址: {self.url}, 错误: {e}")
        
        # 浏览器相关属性
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 配置参数
        # 默认超时30秒，可通过环境变量 PLAYWRIGHT_TIMEOUT 覆盖（单位：毫秒）
        self.timeout = int(os.getenv('PLAYWRIGHT_TIMEOUT', '30000'))  # 毫秒
        self.default_wait = 5  # 默认等待时间
        
        logger.info("BaseDriver 初始化完成")

    def start_browser(self, 
                      browser_type: Literal['chromium', 'firefox', 'webkit'] = 'chromium',
                      headless: bool = False,
                      slow_mo: int = 0,
                      viewport: Optional[Dict[str, int]] = None,
                      timeout: Optional[int] = None,
                      **kwargs) -> Page:
        """启动浏览器并访问配置的URL
        
        Args:
            browser_type: 浏览器类型 ('chromium', 'firefox', 'webkit')
            headless: 是否无头模式（True=无界面，False=有界面）
            slow_mo: 慢动作延迟（毫秒），便于调试
            viewport: 视口大小，如 {'width': 1920, 'height': 1080}
            timeout: 页面加载超时时间（毫秒）
            **kwargs: 其他浏览器启动参数
        
        Returns:
            Page: Playwright 页面对象
        
        Raises:
            Exception: 浏览器启动失败或页面访问失败时抛出
        """
        try:
            # 启动 Playwright
            self.playwright = sync_playwright().start()
            logger.info(f"Playwright 启动成功，浏览器类型: {browser_type}")
            
            # 选择浏览器启动器
            if browser_type == 'chromium':
                browser_launcher = self.playwright.chromium
            elif browser_type == 'firefox':
                browser_launcher = self.playwright.firefox
            elif browser_type == 'webkit':
                browser_launcher = self.playwright.webkit
            else:
                raise ValueError(f"不支持的浏览器类型: {browser_type}")
            
            # 启动浏览器
            launch_options = {
                'headless': headless,
                'slow_mo': slow_mo,
            }
            # 添加其他可选参数
            if kwargs.get('channel'):  # 使用 Chrome 或 Edge
                launch_options['channel'] = kwargs['channel']
            if kwargs.get('args'):  # 启动参数
                launch_options['args'] = kwargs['args']
            
            self.browser = browser_launcher.launch(**launch_options)
            logger.info(f"浏览器启动成功 (headless={headless}, slow_mo={slow_mo}ms)")
            
            # 创建浏览器上下文
            context_options = {}
            if viewport:
                context_options['viewport'] = viewport
            else:
                # 默认最大化窗口效果
                context_options['viewport'] = {'width': 1920, 'height': 1080}
            
            if kwargs.get('record_video'):  # 录制视频
                context_options['record_video_dir'] = 'reports/videos/'
            
            self.context = self.browser.new_context(**context_options)
            logger.info(f"浏览器上下文创建成功，视口大小: {context_options.get('viewport')}")
            
            # 创建新页面
            self.page = self.context.new_page()
            
            # 设置默认超时（优先使用入参 timeout，否则使用实例的 self.timeout）
            if timeout:
                self.timeout = timeout
            # 将超时应用到页面（毫秒）
            try:
                self.page.set_default_timeout(self.timeout)
            except Exception:
                # 忽略无法设置超时的情况
                pass
            
            # 访问页面
            logger.info(f"正在访问页面: {self.url}")
            self.page.goto(self.url, timeout=self.timeout, wait_until="domcontentloaded")
            logger.info(f"页面加载成功: {self.url}")
            
            # 可选：最大化窗口（通过设置视口实现）
            if viewport is None and not kwargs.get('skip_maximize'):
                self.maximize_window()
            
            logger.info("浏览器启动和页面加载完成")
            return self.page
            
        except PlaywrightTimeoutError as e:
            logger.error(f"页面加载超时: {e}")
            self.close_browser()
            raise TimeoutError(f"页面加载超时 (URL: {self.url})") from e
        except Exception as e:
            logger.error(f"启动浏览器或访问页面时发生异常: {e}")
            self.close_browser()
            raise

    def maximize_window(self):
        """最大化窗口效果（通过调整视口）"""
        try:
            # 获取屏幕尺寸
            screen_size = self.page.evaluate("""
                () => ({
                    width: screen.availWidth,
                    height: screen.availHeight
                })
            """)
            self.page.set_viewport_size({
                'width': screen_size['width'],
                'height': screen_size['height']
            })
            logger.info(f"窗口已最大化: {screen_size['width']}x{screen_size['height']}")
        except Exception as e:
            logger.warning(f"最大化窗口失败: {e}")
            # 使用默认大尺寸
            self.page.set_viewport_size({'width': 1920, 'height': 1080})

    def close_browser(self):
        """关闭浏览器并清理资源"""
        try:
            if self.page:
                self.page.close()
                logger.debug("页面已关闭")
        except Exception as e:
            logger.debug(f"关闭页面时出错（可忽略）: {e}")
        
        try:
            if self.context:
                self.context.close()
                logger.debug("浏览器上下文已关闭")
        except Exception as e:
            logger.debug(f"关闭上下文时出错（可忽略）: {e}")
        
        try:
            if self.browser:
                self.browser.close()
                logger.debug("浏览器已关闭")
        except Exception as e:
            logger.debug(f"关闭浏览器时出错（可忽略）: {e}")
        
        try:
            if self.playwright:
                self.playwright.stop()
                logger.debug("Playwright 已停止")
        except Exception as e:
            logger.debug(f"停止 Playwright 时出错（可忽略）: {e}")
        
        logger.info("浏览器资源已全部清理")

    def restart_browser(self, **kwargs) -> Page:
        """重启浏览器
        
        Returns:
            Page: 新的页面对象
        """
        logger.info("正在重启浏览器...")
        self.close_browser()
        time.sleep(2)  # 等待资源释放
        return self.start_browser(**kwargs)

    def new_page(self) -> Page:
        """创建新页面（同一浏览器上下文）
        
        Returns:
            Page: 新创建的页面对象
        """
        if not self.context:
            raise Exception("浏览器上下文未初始化，请先调用 start_browser()")
        
        new_page = self.context.new_page()
        logger.info("新页面创建成功")
        return new_page

    def switch_to_page(self, index: int = -1) -> Page:
        """切换到指定页面
        
        Args:
            index: 页面索引，-1表示最后一个
        
        Returns:
            Page: 切换后的页面对象
        """
        if not self.context:
            raise Exception("浏览器上下文未初始化")
        
        pages = self.context.pages
        if not pages:
            raise Exception("没有可用的页面")
        
        self.page = pages[index]
        logger.info(f"切换到页面索引: {index}, 当前共 {len(pages)} 个页面")
        return self.page

    def take_screenshot(self, name: Optional[str] = None) -> str:
        """截图
        
        Args:
            name: 截图文件名（不含扩展名）
        
        Returns:
            str: 截图保存路径
        """
        if not self.page:
            raise Exception("页面未初始化")
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}" if name else f"screenshot_{timestamp}"
        
        # 确保目录存在
        screenshot_dir = "reports/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        
        filepath = os.path.join(screenshot_dir, f"{filename}.png")
        self.page.screenshot(path=filepath, full_page=True)
        logger.info(f"截图已保存: {filepath}")
        return filepath

    def wait_for_timeout(self, seconds: int):
        """等待指定秒数（仅用于必要场景）
        
        Args:
            seconds: 等待秒数
        """
        logger.debug(f"等待 {seconds} 秒...")
        time.sleep(seconds)

    def get_page_info(self) -> Dict[str, Any]:
        """获取当前页面信息
        
        Returns:
            Dict: 包含URL、标题等信息的字典
        """
        if not self.page:
            return {}
        
        return {
            'url': self.page.url,
            'title': self.page.title(),
            'viewport': self.page.viewport_size
        }

    def open_url_with_login(self,
                             url: Optional[str] = None,
                             login_check_selector: Optional[str] = None,
                             login_check_fn: Optional[Callable[[Page], bool]] = None,
                             login_fn: Optional[Callable[[Page], None]] = None,
                             timeout: Optional[int] = None) -> Page:
        """打开指定 URL，并在需要时执行登录。

        逻辑：
        - 如果提供 `url` 参数则使用它，否则使用实例的 `self.url`。
        - 打开页面并等待网络空闲。
        - 按顺序使用 `login_check_selector`、`login_check_fn` 判断是否已登录。
        - 如果判断为未登录且提供了 `login_fn`，则调用 `login_fn(self.page)` 执行登录流程。

        参数：
            url: 可选的目标 URL。
            login_check_selector: 用于判断登录状态的 CSS 选择器（存在则视为已登录）。
            login_check_fn: 自定义检查函数，接收 `Page` 并返回 bool（True 表示已登录）。
            login_fn: 登录函数，接收 `Page`，负责执行登录并切换到登录后页面。
            timeout: 超时时间（毫秒），覆盖实例默认值。

        返回：
            当前 `Page` 对象（登录后仍会返回同一个 page）。
        """
        if url:
            self.url = url

        if not self.page:
            raise Exception("页面未初始化，请先调用 start_browser() 或在已创建的 context 中创建 page")

        use_timeout = timeout or self.timeout
        # 打开页面
        logger.info(f"打开页面 (login-check): {self.url}")
        self.page.goto(self.url, timeout=use_timeout)
        try:
            self.page.wait_for_load_state("networkidle", timeout=use_timeout)
        except Exception:
            # 若等待超时仍继续后续检查（有些应用不会触发 networkidle）
            logger.debug("等待 networkidle 超时，继续进行登录检查")

        # 1) 通过 selector 检查（最简单快捷）
        try:
            if login_check_selector:
                loc = self.page.locator(login_check_selector)
                try:
                    if loc.count() > 0:
                        logger.info("检测到登录标志（selector），视为已登录")
                        return self.page
                except Exception:
                    # count 可能不可用，尝试 first
                    try:
                        if loc.first:
                            logger.info("检测到登录标志（selector.first），视为已登录")
                            return self.page
                    except Exception:
                        pass

            # 2) 自定义检查函数
            if login_check_fn:
                try:
                    ok = login_check_fn(self.page)
                    if ok:
                        logger.info("自定义登录检查函数返回已登录")
                        return self.page
                except Exception as e:
                    logger.debug(f"执行 login_check_fn 时出错: {e}")

            # 3) 简单基于 URL 的判断：若当前 URL 含有登录路径片段，视为未登录
            cur_url = self.page.url or ''
            if any(x in cur_url for x in ['/login', '/auth/login']):
                logger.info("当前 URL 指向登录页，视为未登录")
            else:
                # 未检测到明确的登录标志，假设已登录
                logger.info("未检测到登录标志，假设已登录")
                return self.page

        except Exception as e:
            logger.debug(f"检查登录状态时发生异常: {e}")

        # 如果到这里仍然认为未登录且提供了 login_fn，则调用登录函数
        if login_fn:
            logger.info("未登录，开始调用登录函数执行登录流程")
            try:
                login_fn(self.page)
                # 登录后等待页面稳定
                try:
                    self.page.wait_for_load_state("networkidle", timeout=use_timeout)
                except Exception:
                    logger.debug("登录后等待 networkidle 超时，继续")
                return self.page
            except Exception as e:
                logger.error(f"执行登录函数失败: {e}")
                raise

        logger.info("未检测到登录状态，且未提供登录函数；返回当前页面以便后续处理")
        return self.page


# 便捷函数：快速获取驱动
def get_driver(url: Optional[str] = None) -> BaseDriver:
    """获取 BaseDriver 实例的便捷函数
    
    Args:
        url: 页面URL（可选）
    
    Returns:
        BaseDriver: 驱动实例
    """
    driver = BaseDriver(url=url)
    driver.start_browser()
    return driver


if __name__ == "__main__":
    # 简单测试
    driver = BaseDriver()
    try:
        page = driver.start_browser()
        logger.info(f"当前页面URL: {page.url}")
        logger.info(f"当前页面标题: {page.title()}")
    finally:
        driver.close_browser()
