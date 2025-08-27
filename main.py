import sys
from time import  time
import traceback
from playwright.sync_api import sync_playwright , TimeoutError
from config import get_config
from utils import parse_to_playwright_cookies




import os
import json

def get_v2ray_config():
    """
    读取并解析当前目录下的 v2ray/config.json 配置文件
    返回字典格式的配置数据
    """
    config_path = os.path.join(".", "v2ray", "config.json")  # 兼容各操作系统的路径格式
    
    try:
        # 检查文件是否存在
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件未找到: {os.path.abspath(config_path)}")
        
        # 检查文件读取权限
        if not os.access(config_path, os.R_OK):
            raise PermissionError(f"无读取权限: {config_path}")

        # 读取文件内容
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            return config_data
            
    except json.JSONDecodeError as e:
        print(f"JSON格式错误（第{e.lineno}行）: {e.msg}")
    except Exception as e:
        print(f"配置读取失败: {type(e).__name__} - {str(e)}")
    
    return None

# 使用示例
def get_v2ray():
    config = get_v2ray_config()
    if config:
        # 打印关键配置信息
        print("="*40 + " V2Ray配置详情 " + "="*40)
        for inbound in config.get("inbounds", []):
            print(f"[监听端口] {inbound.get('port')}")
            print(f"[协议类型] {inbound.get('protocol')}")
            print("-"*60)
    else:
        print("未能获取有效配置")

get_v2ray()



print('开始执行...')
start_time = time()
with sync_playwright() as playwright:
    try:
        config = get_config()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(proxy={"server": config['proxy']})
        context.add_cookies(parse_to_playwright_cookies(config['cookies']))

        page = context.new_page()

        page.goto("https://www.douyin.com/?recommend=1")

        print('等待弹窗1')
        # 询问是否保存登陆信息 关闭
        try:
            page.get_by_text("取消").click(timeout=100000)
            print('点击私信按钮')
            page.get_by_role("paragraph").filter(has_text="私信").click()
        except TimeoutError:
            print('点击私信按钮')
            page.get_by_role("paragraph").filter(has_text="私信").click()

        print('点击续火花用户')
        page.get_by_text(f"{config['nickname']}",exact=True).first.click()
        print('输入文本并回车')
        page.locator("#douyin-header-menuCt").get_by_role("textbox").locator("div").nth(2).click()
        page.locator("#douyin-header-menuCt").get_by_role("textbox").fill(f"{config['msg']}")
        page.locator("#douyin-header-menuCt").get_by_role("textbox").press("Enter")

        try:
            page.locator("text=发送失败").wait_for(timeout=10000)
            print('发送失败！')
            raise RuntimeError('发送失败!')
        except TimeoutError as e:
            print('发送成功！')

        print("耗时："+str(int(time() - start_time)))
        # sleep(10)

        print('关闭浏览器')

        context.close()
        browser.close()
    except Exception as e:
    # error_msg = str(e)
        error_details = traceback.format_exc()
        print(error_details)

        try :
            screenshot = page.screenshot(path='error.png',full_page=True)
        except Exception as e:
            print(e)

        sys.exit(1)
