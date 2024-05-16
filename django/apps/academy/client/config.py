import base64

from httpx import Client

from django.conf import settings


class AcademyClientConfig:
    timeout: float = 10.0
    max_retries: int = 3

    @staticmethod
    def get_client() -> Client:
        base_url = (academy_settings := getattr(settings, "ACADEMY_SETTINGS", {})).get("BASE_URL")
        password = academy_settings.get("ACADEMY_PASSWORD")
        username = academy_settings.get("ACADEMY_USERNAME")
        basic_auth = base64.b64encode(f"{username}:{password}".encode()).decode()

        if not academy_settings:
            raise ValueError("Academy Settings not found in the settings")

        return Client(
            timeout=AcademyClientConfig.timeout,
            headers={
                "Authorization": f"Basic {basic_auth}",
            },
            base_url=base_url,
        )
