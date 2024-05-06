from flex_pubsub.subscription import SubscriptionBase


class AccountSubscription(SubscriptionBase):
    EMAILING = "emailing"
    ASSISTANTS = "assistants"


class CVSubscription(SubscriptionBase):
    CV = "resume"
