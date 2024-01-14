from typing import Literal, TypedDict

from .types import GetScoresResponse


class WebhookHandlerResponse(TypedDict):
    status: str


class WebhookHandler:
    def handle_event(self, event: Literal["scores_update"], payload: dict) -> WebhookHandlerResponse:
        if event == "scores_update":
            return self.handle_scores_update(payload)
        else:
            raise ValueError(f"Unknown event type: {event}")

    def handle_scores_update(self, payload: dict) -> WebhookHandlerResponse:
        validated_payload = GetScoresResponse.model_validate(payload)
        return {"status": f"Scores update for order {validated_payload} processed successfully."}
