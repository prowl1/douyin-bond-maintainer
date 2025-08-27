import sys
from time import  time
import traceback
from playwright.sync_api import sync_playwright , TimeoutError
from config import get_config
from utils import parse_to_playwright_cookies



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

        print('处理可能出现的弹窗')
        # 询问是否保存登陆信息 关闭（可忽略失败）
        try:
            page.get_by_text("取消", exact=True).click(timeout=3000)
        except Exception:
            pass

        # 点击进入私信/消息页：尝试多种定位策略
        print('尝试点击私信入口')
        dm_clicked = False
        dm_locators = [
            lambda: page.get_by_text("私信", exact=True),
            lambda: page.get_by_role("link", name="私信"),
            lambda: page.locator("p:has-text(\"私信\")"),
            lambda: page.locator("text=私信")
        ]
        for get_loc in dm_locators:
            try:
                loc = get_loc()
                loc.first.click(timeout=5000)
                dm_clicked = True
                break
            except Exception:
                continue

        if not dm_clicked:
            # 作为兜底：尝试直接跳转到消息页面（如果地址可用）
            try:
                page.goto("https://www.douyin.com/im?recommend=1")
                page.wait_for_load_state("domcontentloaded")
                dm_clicked = True
            except Exception:
                pass

        if not dm_clicked:
            page.screenshot(path='error.png', full_page=True)
            raise RuntimeError('无法定位或进入私信页')

        print('点击续火花用户')
        contact_clicked = False
        try:
            page.get_by_text(f"{config['nickname']}", exact=True).first.click(timeout=8000)
            contact_clicked = True
        except Exception:
            # 放宽匹配策略
            try:
                page.locator(f"div:has-text(\"{config['nickname']}\")").first.click(timeout=5000)
                contact_clicked = True
            except Exception:
                pass

        if not contact_clicked:
            page.screenshot(path='error.png', full_page=True)
            raise RuntimeError(f"未找到联系人: {config['nickname']}")

        print('输入文本并回车')
        # 更稳健地获取输入框
        input_box = None
        try:
            input_box = page.locator('[contenteditable="true"]').last
            input_box.click(timeout=5000)
        except Exception:
            try:
                input_box = page.get_by_role("textbox").last
                input_box.click(timeout=5000)
            except Exception:
                page.screenshot(path='error.png', full_page=True)
                raise RuntimeError('未找到输入框')

        # 对 contenteditable，优先使用 keyboard.type 更可靠
        page.keyboard.type(f"{config['msg']}")
        page.keyboard.press("Enter")

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

        # 当异常发生在创建 page 之前时，避免引用未定义的 page
        try:
            if 'page' in locals() and page is not None:
                page.screenshot(path='error.png', full_page=True)
        except Exception as e:
            print(e)

        sys.exit(1)
