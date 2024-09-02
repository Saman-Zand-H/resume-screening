from flex_pubsub.subscription import SubscriptionBase


class AccountSubscription(SubscriptionBase):
    EMAILING = "emailing"
    ASSISTANTS = "assistants"
    DOCUMENT_VERIFICATION = "document_verification"


class CVSubscription(SubscriptionBase):
    CV = "resume"


class NotificationSubscription(SubscriptionBase):
    CAMPAIGN = "campaign"
