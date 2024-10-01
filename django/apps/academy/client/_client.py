import httpx
from pydantic import BaseModel, ValidationError

from .config import AcademyClientConfig
from .exceptions import EXCEPTIONS, AcademyRequestException

from common.logging import get_logger

logger = get_logger()


class BaseAcademyClient:
    def __init__(self):
        self.client = AcademyClientConfig.get_client()
        self.max_retries = AcademyClientConfig.max_retries

    def _make_request[T: BaseModel](
        self,
        method: str,
        endpoint: str,
        model: T,
        **kwargs,
    ) -> T:
        retries = 0
        url = f"{self.client.base_url}{endpoint}"
        response = self._send_request_with_retries(method, url, retries, **kwargs)
        return self._parse_response(response, model)

    def _send_request_with_retries(self, method: str, url: str, retries: int, **kwargs) -> httpx.Response:
        while retries < self.max_retries:
            try:
                response = self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.TimeoutException as e:
                retries += 1
                if retries >= self.max_retries:
                    raise AcademyRequestException(f"Request to {url} failed after {self.max_retries} retries") from e
                logger.warning(f"Retrying request to {url} due to {e}, attempt {retries}/{self.max_retries}")
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                exception = EXCEPTIONS.get(e.response.status_code, AcademyRequestException)
                raise exception(e.response.text) from e

    def _parse_response[T: BaseModel](self, response: httpx.Response, model: T) -> T:
        try:
            return model.model_validate(response.json())
        except ValidationError as e:
            logger.error(f"Failed to parse response: {e}")
            raise AcademyRequestException("Failed to parse response") from e
