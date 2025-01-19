import os
import tempfile
import time
from io import BytesIO

from common.logging import get_logger
from pydantic import HttpUrl, RootModel
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from django.core.files.base import ContentFile

logger = get_logger()


def download_file(report_link, *, is_headless=True, download_wait_time=30, timeout=60) -> BytesIO:
    with tempfile.TemporaryDirectory() as download_dir:
        chrome_options = Options()
        if is_headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")

        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
            "plugins.always_open_pdf_externally": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        driver = None
        try:
            logger.info(f"Initializing Chrome WebDriver for URL: {report_link}")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(str(report_link))

            logger.info(f"Navigated to page with title: {driver.title}")

            selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download')]",
                "//button[contains(@class, 'download')]",
                "//a[contains(@class, 'download')]",
                "//button[contains(@id, 'download')]",
                "//a[contains(@id, 'download')]",
                "//input[@type='button'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download')]",
                "//input[@type='submit'][contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download')]",
            ]

            selector_timeout = max(5, timeout // len(selectors))
            download_button = None
            for selector in selectors:
                try:
                    logger.info(f"Trying selector: {selector}")
                    download_button = WebDriverWait(driver, selector_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"Found download button with selector: {selector}")
                    time.sleep(1)
                    break
                except TimeoutException:
                    logger.info(f"Selector not found: {selector}")
                    continue
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {str(e)}")
                    continue

            if not download_button:
                try:
                    logger.info("Trying fallback approach for finding download button")
                    elements = driver.find_elements(
                        By.XPATH,
                        "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download')]",
                    )
                    if elements:
                        logger.info(f"Found {len(elements)} potential download elements")
                        for element in elements:
                            try:
                                if element.is_displayed() and element.is_enabled():
                                    logger.info(f"Attempting to click fallback element: {element.tag_name}")
                                    download_button = element
                                    break
                            except BaseException:
                                continue
                except Exception as e:
                    logger.warning(f"Error with fallback approach: {str(e)}")

                if not download_button:
                    try:
                        screenshot_path = os.path.join(download_dir, "screenshot.png")
                        driver.save_screenshot(screenshot_path)
                        logger.info(f"Screenshot saved to: {screenshot_path}")
                    except Exception as e:
                        logger.warning(f"Failed to take screenshot: {str(e)}")

                    raise TimeoutException("Download button not found on the page")

            logger.info("Clicking download button")
            download_button.click()
            logger.info("Download button clicked")

            start_time = time.time()
            downloaded_file_path = None

            logger.info(f"Waiting for file to be downloaded (timeout: {download_wait_time}s)")
            while time.time() - start_time < download_wait_time:
                downloaded_files = [f for f in os.listdir(download_dir) if not f.endswith(".crdownload")]
                if downloaded_files:
                    downloaded_file_path = os.path.join(download_dir, downloaded_files[0])
                    logger.info(f"Found file: {downloaded_file_path}")
                    if not any(f.endswith(".crdownload") for f in os.listdir(download_dir)):
                        logger.info("Download completed")
                        break
                time.sleep(1)

            if not downloaded_file_path:
                dir_contents = os.listdir(download_dir)
                logger.error(f"No files were downloaded. Directory contents: {dir_contents}")
                raise FileNotFoundError("No files were downloaded within the specified time limit.")

            file_size = 0
            prev_size = -1
            size_stable_count = 0

            logger.info("Waiting for file size to stabilize")
            while time.time() - start_time < download_wait_time:
                prev_size = file_size
                file_size = os.path.getsize(downloaded_file_path)

                if file_size == prev_size:
                    size_stable_count += 1
                    if size_stable_count >= 3:
                        break
                else:
                    size_stable_count = 0

                logger.info(f"Current file size: {file_size} bytes")
                time.sleep(1)

            logger.info(f"Reading file: {downloaded_file_path}")
            with open(downloaded_file_path, "rb") as f:
                pdf_bytes = BytesIO(f.read())
            logger.info(f"File read successfully, size: {len(pdf_bytes.getvalue())} bytes")
            return pdf_bytes

        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            if driver:
                try:
                    page_source = driver.page_source[:1000] + "..." if driver.page_source else "N/A"
                    logger.error(f"Page source excerpt: {page_source}")
                except BaseException:
                    pass
            raise Exception(f"Error downloading file from {report_link}: {str(e)}")

        finally:
            if driver:
                try:
                    logger.info("Quitting WebDriver")
                    driver.quit()
                except WebDriverException as e:
                    logger.warning(f"Error quitting WebDriver: {str(e)}")


def download_report_file(report_link: RootModel[HttpUrl], file_name: str):
    logger.info(f"Starting download of report file: {file_name} from {report_link}")
    try:
        pdf_file = download_file(report_link)
        return ContentFile(pdf_file.read(), name=file_name)
    except Exception as e:
        logger.error(f"Error in download_report_file: {e}")
        raise
