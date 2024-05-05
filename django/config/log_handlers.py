import logging
from google.cloud import storage
from django.utils import timezone


class GCSHandler(logging.Handler):
    def __init__(self, bucket_name, log_file_name, settings):
        super().__init__()
        environment = settings.split(".")[-1]
        self.bucket_name = f"{environment}-{bucket_name}"
        self.log_file_name = log_file_name
        self.client = storage.Client()

    def emit(self, record):
        log_entry = self.format(record)
        bucket = self.client.get_bucket(self.bucket_name)

        today = timezone.now().strftime("%Y-%m-%d")
        timestamp = timezone.now().strftime("%H:%M:%S")
        blob_name = f"{self.log_file_name}_{today}.log"
        blob = bucket.blob(blob_name)

        if blob.exists():
            existing_data = blob.download_as_text()
            divider = "=" * 100
            log_entry = f"{existing_data}\n{divider}\n{timestamp}: {log_entry}"
        else:
            log_entry = f"{timestamp}: {log_entry}"

        blob.upload_from_string(log_entry, content_type="text/plain")
