import re

from django.conf import settings


def get_static_base_url():
    static_base_url = "http://localhost:8000"
    site_domain = settings.SITE_DOMAIN and re.sub(r"https?://", "", settings.SITE_DOMAIN)

    if site_domain and "localhost" not in site_domain:
        static_base_url = f"https://{settings.SITE_DOMAIN}"
    return static_base_url
