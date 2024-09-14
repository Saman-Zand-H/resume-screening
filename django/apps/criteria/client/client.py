from ._client import BaseCriteriaClient
from .types import (
    CreateOrderRequest,
    CreateOrderResponse,
    GetScoreRequest,
    GetScoresResponse,
    GetStatusRequest,
    GetStatusResponse,
    PackagesResponse,
)

from common.logging import get_logger

logger = get_logger()


class CriteriaClient(BaseCriteriaClient):
    def get_packages(self) -> PackagesResponse:
        return self._make_request("GET", "packages", model=PackagesResponse)

    def create_order(self, order_data: CreateOrderRequest) -> CreateOrderResponse:
        return self._make_request(
            "POST", "order", model=CreateOrderResponse, json=order_data.model_dump(exclude_unset=True)
        )

    def get_status(self, order_id: GetStatusRequest) -> GetStatusResponse:
        return self._make_request(
            "GET",
            f"status?orderId={order_id.root}",
            model=GetStatusResponse,
        )

    def get_scores(self, order_id: GetScoreRequest) -> GetScoresResponse:
        return self._make_request(
            "GET",
            f"scores?orderId={order_id.root}",
            model=GetScoresResponse,
        )


criteria_client = CriteriaClient()
