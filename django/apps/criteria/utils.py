import os
import tempfile
import time
from io import BytesIO

from pydantic import HttpUrl, RootModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from django.core.files.base import ContentFile


def download_file(report_link: RootModel[HttpUrl], *, is_headless=True, download_wait_time=10):
    with tempfile.TemporaryDirectory() as download_dir:
        chrome_options = Options()
        if is_headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) CPJ/1.0 Safari/537.36"
        )

        prefs = {"download.default_directory": download_dir}
        chrome_options.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        try:
            driver.get(report_link)
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Download')]"))
            )
            download_button.click()
            time.sleep(download_wait_time)

            if not (downloaded_files := os.listdir(download_dir)):
                raise FileNotFoundError("No files were downloaded.")

            downloaded_file_path = os.path.join(download_dir, downloaded_files[0])

            with open(downloaded_file_path, "rb") as f:
                pdf_bytes = BytesIO(f.read())

            return pdf_bytes

        finally:
            driver.quit()


def download_report_file(report_link: RootModel[HttpUrl], file_name: str):
    pdf_file = download_file(report_link)

    return ContentFile(pdf_file.read(), name=file_name)
