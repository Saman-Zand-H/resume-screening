import os
import tempfile
import time
from io import BytesIO

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


def download_file(report_link, *, is_headless=True, download_wait_time=20, timeout=30) -> BytesIO:
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
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(str(report_link))

            selectors = [
                "//button[contains(text(),'Download')]",
                "//a[contains(text(),'Download')]",
                "//button[contains(@class,'download')]",
                "//a[contains(@class,'download')]",
                "//button[contains(@id,'download')]",
                "//a[contains(@id,'download')]",
            ]

            download_button = None
            for selector in selectors:
                try:
                    download_button = WebDriverWait(driver, timeout // len(selectors)).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not download_button:
                raise TimeoutException("Download button not found on the page")

            download_button.click()

            start_time = time.time()
            downloaded_file_path = None

            while time.time() - start_time < download_wait_time:
                downloaded_files = [f for f in os.listdir(download_dir) if not f.endswith(".crdownload")]
                if downloaded_files:
                    downloaded_file_path = os.path.join(download_dir, downloaded_files[0])
                    if not any(f.endswith(".crdownload") for f in os.listdir(download_dir)):
                        break
                time.sleep(0.5)

            if not downloaded_file_path:
                raise FileNotFoundError("No files were downloaded within the specified time limit.")

            file_size = 0
            prev_size = -1

            while file_size != prev_size and time.time() - start_time < download_wait_time:
                prev_size = file_size
                file_size = os.path.getsize(downloaded_file_path)
                time.sleep(0.5)

            with open(downloaded_file_path, "rb") as f:
                pdf_bytes = BytesIO(f.read())
            return pdf_bytes

        except Exception as e:
            raise Exception(f"Error downloading file: {str(e)}")

        finally:
            if not driver:
                return

            try:
                driver.quit()
            except WebDriverException:
                pass


def download_report_file(report_link: RootModel[HttpUrl], file_name: str):
    pdf_file = download_file(report_link)

    return ContentFile(pdf_file.read(), name=file_name)
