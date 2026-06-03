#!/usr/bin/env python3
"""从 Python 运行 pytest，便于使用 `python run_tests.py`。

用法:
    python run_tests.py                # 静默运行 TestCase/test_homepage.py
    python run_tests.py -q             # 直接传递 pytest 参数
    python run_tests.py --alluredir=reports/allure-results

如果设置环境变量 `ALLURE=1`，脚本会在未提供时自动添加
`--alluredir=reports/allure-results`。
"""
import os
import sys

import pytest
import subprocess
import shutil
import urllib.request
import json
from datetime import datetime


def _restart_http_server(report_dir: str, port: int = 8000):
    """杀掉旧 HTTP 进程，启动新 HTTP 服务指向 reports/ 目录（包含报告子目录）。"""
    # 杀掉旧进程
    subprocess.run(
        ["fuser", "-k", f"{port}/tcp"],
        capture_output=True, timeout=5,
    )
    print(f"已清理端口 {port}")

    # reports/ 父目录
    parent_dir = os.path.dirname(report_dir)

    # 启动新 HTTP 服务（后台进程，不阻塞）
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--directory", parent_dir],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"HTTP 服务已启动: http://localhost:{port}/")
    return server_proc


def _notify_feishu(root: str, report_dir: str, http_port: int = 8000):
    """读取 config.ini 中的 webhook_url，将报告的访问地址发送到飞书群。"""
    # 读取 webhook_url
    try:
        from common.readConfig import ReadConfig
        config = ReadConfig()
        webhook_url = config.read_config('webhook', 'webhook_url')
    except Exception as e:
        print(f"读取 webhook_url 失败（跳过发送至飞书）: {e}")
        return

    if not webhook_url or not webhook_url.startswith("http"):
        print("webhook_url 无效（跳过发送至飞书）")
        return

    # 重启 HTTP 服务指向新报告
    _restart_http_server(report_dir, http_port)

    # 构建消息内容：HTTP 访问地址（含报告子目录名）
    report_name = os.path.basename(report_dir)
    http_url = f"http://localhost:{http_port}/{report_name}/index.html"
    msg = f"测试报告已生成：\n{http_url}"

    # 发送到飞书 webhook
    try:
        payload = json.dumps({
            "msg_type": "text",
            "content": {"text": msg}
        }).encode('utf-8')
        req = urllib.request.Request(webhook_url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"飞书通知发送成功: {resp.status}")
    except Exception as e:
        print(f"发送飞书通知失败: {e}")


def main(argv=None):
    root = os.path.dirname(os.path.abspath(__file__))
    # 确保项目根目录在 sys.path 中
    if root not in sys.path:
        sys.path.insert(0, root)

    argv = list(argv or sys.argv[1:])
    if not argv:
        # 默认：运行主页测试
        argv = ["-q", "TestCase/test_homepage.py"]

    # 默认启用 Allure 报告（除非显式设置 ALLURE=0）
    if os.getenv("ALLURE", "1") != "0" and not any(a.startswith("--alluredir") for a in argv):
        argv.append("--alluredir=reports/allure-results")

    # 运行 pytest 前清空旧的 allure 结果，避免累积上次的运行结果
    results_dir = None
    for i, a in enumerate(argv):
        if a.startswith("--alluredir"):
            if "=" in a:
                results_dir = a.split("=", 1)[1]
            elif i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                results_dir = argv[i + 1]
    if not results_dir:
        results_dir = os.path.join(root, "reports", "allure-results")

    # 清空旧结果目录
    if os.path.isdir(results_dir):
        try:
            shutil.rmtree(results_dir)
        except Exception:
            pass

    # 运行 pytest 并获取退出码
    exit_code = pytest.main(argv)

    # 如果存在结果，则尝试生成带时间戳的 HTML 报告
    try:
        if os.path.isdir(results_dir) and os.listdir(results_dir):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_dir = os.path.join(root, "reports", f"allure-report-{ts}")
            os.makedirs(os.path.dirname(out_dir), exist_ok=True)

            # 尝试使用本地 allure CLI 生成报告
            cmd = ["allure", "generate", results_dir, "-o", out_dir, "--clean"]
            print("Generating Allure report:", " ".join(cmd))
            try:
                proc = subprocess.run(cmd, check=False)
                if proc.returncode == 0:
                    print(f"Allure report generated: {out_dir}")
                else:
                    print("Allure CLI 返回非零退出码；报告可能未生成。")
            except FileNotFoundError:
                print("未在 PATH 中找到 Allure CLI；跳过 HTML 报告生成。")

            # 清理旧报告：保留最近 10 个以 allure-report- 开头的目录
            reports_root = os.path.join(root, "reports")
            try:
                entries = []
                for name in os.listdir(reports_root):
                    if name.startswith("allure-report-"):
                        full = os.path.join(reports_root, name)
                        if os.path.isdir(full):
                            entries.append((full, os.path.getmtime(full)))
                # 按修改时间降序排序（最新的在前）
                entries.sort(key=lambda x: x[1], reverse=True)
                # 保留最近 10 个
                to_remove = entries[10:] 
                for full, _ in to_remove:
                    try:
                        print(f"删除旧报告: {full}")
                        shutil.rmtree(full)
                    except Exception as e:
                        print(f"删除 {full} 失败: {e}")
            except FileNotFoundError:
                pass

            # 将截图复制到报告中的 screenshots 目录
            src_screenshots = os.path.join(root, "reports", "screenshots")
            dst_screenshots = os.path.join(out_dir, "screenshots")
            if os.path.isdir(src_screenshots) and os.listdir(src_screenshots):
                try:
                    os.makedirs(dst_screenshots, exist_ok=True)
                    for fname in os.listdir(src_screenshots):
                        src_file = os.path.join(src_screenshots, fname)
                        if os.path.isfile(src_file):
                            shutil.copy2(src_file, os.path.join(dst_screenshots, fname))
                    print(f"截图已复制到: {dst_screenshots}")
                except Exception as e:
                    print(f"复制截图至报告目录失败: {e}")

            # 打包报告并发送到飞书 webhook
            _notify_feishu(root, out_dir)
    except Exception as e:
        # 不要让报告生成失败掩盖测试失败，但记录异常以便排查
        try:
            import traceback

            print(f"生成 Allure 报告或清理报告时发生异常: {e}")
            traceback.print_exc()
        except Exception:
            # 最后兜底：如果打印也失败，静默忽略
            pass

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
