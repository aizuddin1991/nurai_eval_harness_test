# nurai_client.py
import os
import time
import yaml
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError, Page, Frame
from bs4 import BeautifulSoup

def load_config(path: str):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def goto_from_home(context, config):
    base_url = config["base_url"]
    selectors = config["selectors"]
    timeout = config.get("timeout", 5000)

    page = context.new_page()
    page.goto(base_url, wait_until="domcontentloaded")

    # Access the locator string
    start_chat_locator = config["selectors"]["home_page"]["start_chat"]["locator"]

    # Expect new tab
    with context.expect_page() as new_page_info:
        # Direct click
        page.click(start_chat_locator, timeout=5000)
    new_page = new_page_info.value
    new_page.wait_for_load_state("domcontentloaded")

    # Try login page
    try:
        new_page.locator(selectors["login"]["username_field"]["locator"]).wait_for(
            state="visible", timeout=3000
        )
        return {"page": new_page, "state": "login"}
    except TimeoutError:
        pass

    # Try chat page
    try:
        chat_input = new_page.locator(selectors["chat_page"]["prompt_input"]["locator"])
        chat_input.wait_for(state="visible", timeout=3000)
        return {"page": new_page, "state": "chat"}
    except TimeoutError:
        pass

    # Fallback: URL-based detection
    url = new_page.url.lower()
    if "login" in url:
        return {"page": new_page, "state": "login"}
    if "chat" in url or "conversation" in url:
        return {"page": new_page, "state": "chat"}

    raise RuntimeError("Navigation ambiguous: neither login nor chat detected.")

def login_if_needed(page, config):
    selectors = config["selectors"]["login"]
    load_dotenv()
    username = os.getenv("LOGIN_USER")
    password = os.getenv("LOGIN_PASS")
    timeout = config.get("timeout", 5000)

    # Fill username/password
    page.locator(selectors["username_field"]["locator"]).fill(username)
    page.locator(selectors["password_field"]["locator"]).fill(password)

    page.locator(selectors["submit_button"]["locator"]).click()

    # Wait a bit for redirect
    time.sleep(config["delays"]["after_login"])

    # Verify chat input appears
    chat_input = page.locator(config["selectors"]["chat_page"]["prompt_input"]["locator"])
    chat_input.wait_for(state="visible", timeout=timeout)
    return {"page": page, "state": "chat"}

def take_snapshot(page: Page, file_name: str, full_page: bool = True):
    """
    Save a snapshot (screenshot) of the current page.

    Args:
        page (Page): The Playwright page object you are working with.
        file_name (str): The output file name (e.g., 'snapshot.png').
        full_page (bool): Whether to capture the full scrollable page.
    """
    page.screenshot(path=file_name, full_page=full_page)
    print(f"Snapshot saved as {file_name}")

def extract_page_source(url: str, output_file: str = "page_source.html"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        html = page.content()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        browser.close()

def extract_selectors_from_current_page(page: Page, output_file: str = "current_page_selectors.txt", limit: int = 10000):
    """
    Extracts selector-relevant attributes from the current page source.
    Dumps results into a human-readable .txt file.
    """
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.find_all(True)  # all tags

    with open(output_file, "w", encoding="utf-8") as f:
        for idx, el in enumerate(elements[:limit]):
            tag = el.name
            element_id = el.get("id")
            element_class = el.get("class")
            name = el.get("name")
            role = el.get("role")
            text = el.get_text(strip=True)[:60]

            selectors = []
            if element_id:
                selectors.append(f"#{element_id}")
            if element_class:
                selectors.append(f"{tag}.{element_class[0]}")
            if name:
                selectors.append(f"{tag}[name='{name}']")
            if role:
                selectors.append(f"[role='{role}']")
            if text:
                selectors.append(f"text={text}")

            f.write(f"Element {idx}:\n")
            f.write(f"  Tag       : {tag}\n")
            f.write(f"  Text      : {text}\n")
            f.write("  Selectors :\n")
            for sel in selectors:
                f.write(f"    - {sel}\n")
            f.write("\n")

def wait_for_latest_answer(page: Page, timeout: int = 60, poll_interval: float = 0.5):
    """
    Waits until the latest AI answer is fully rendered by monitoring the last markdown-body content.
    Returns the final inner_text.
    """
    container = page.locator("div.ai-message-container").nth(-1)
    answer_box = container.locator("div.ai-message-content div.markdown-body")

    # Wait for visibility
    answer_box.wait_for(state="visible", timeout=timeout * 1000)

    # Poll until content stabilizes
    previous = ""
    stable_count = 0
    start_time = time.time()

    while time.time() - start_time < timeout:
        current = answer_box.inner_text().strip()
        if current == previous:
            stable_count += 1
        else:
            stable_count = 0
            previous = current

        if stable_count >= 3:  # content hasn't changed for 3 cycles
            break

        time.sleep(poll_interval)

    return current

def dump_ai_answer_to_file(page: Page, output_file: str = "ai_answer.txt", timeout: int = 60, poll_interval: float = 0.5):
    """
    Uses wait_for_latest_answer to get the final AI response,
    then dumps it into a text file.
    """
    answer = wait_for_latest_answer(page, timeout=timeout, poll_interval=poll_interval)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(answer)

# Example usage
if __name__ == "__main__":
    config = load_config("configs/prod.yml")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        result = goto_from_home(context, config)
        if result["state"] == "login":
            result = login_if_needed(result["page"], config)
        print("Final state:", result["state"])
        browser.close()
