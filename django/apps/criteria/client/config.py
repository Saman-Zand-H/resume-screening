from httpx import Client

from django.conf import settings


class CriteriaClientConfig:
    timeout: float = 10.0
    max_retries: int = 3

    @staticmethod
    def get_client() -> Client:
        base_url = (criteria_settings := getattr(settings, "CRITERIA_SETTINGS", {})).get("BASE_URL")
        auth_token = criteria_settings.get("AUTH_TOKEN")
        auth_type = criteria_settings.get("AUTH_TYPE")
        if not criteria_settings:
            raise ValueError("Criteria Settings not found in the settings")

        return Client(
            timeout=CriteriaClientConfig.timeout,
            headers={
                "Authorization": f"{auth_type} {auth_token}",
            },
            base_url=base_url,
        )
