from flex_pubsub.subscription import SubscriptionBase


class AccountSubscription(SubscriptionBase):
    EMAILING = "emailing"
    ASSISTANTS = "assistants"
    DAILY_EXECUTION = "daily_execution"


class CVSubscription(SubscriptionBase):
    CV = "resume"


class NotificationSubscription(SubscriptionBase):
    CAMPAIGN = "campaign"
