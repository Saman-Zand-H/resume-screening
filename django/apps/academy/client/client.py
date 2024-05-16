import logging
from typing import Any

from ._client import BaseAcademyClient

logger = logging.getLogger(__name__)


class AcademyClient(BaseAcademyClient):
    def test(test_params: Any) -> Any:
        pass


academy_client = AcademyClient()
