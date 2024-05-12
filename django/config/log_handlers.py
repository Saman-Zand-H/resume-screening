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
        log_entry = getattr(record, "html_error", None)
        if not log_entry:
            return
        bucket = self.client.get_bucket(self.bucket_name)

        timestamp = timezone.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        blob_name = f"errors/{timestamp}.html"

        blob = bucket.blob(blob_name)
        blob.upload_from_string(log_entry, content_type="text/html")
