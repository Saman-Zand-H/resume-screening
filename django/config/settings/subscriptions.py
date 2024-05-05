from flex_pubsub.subscription import SubscriptionBase


class AccountSubscription(SubscriptionBase):
    EMAILING = "emailing"


class CVSubscription(SubscriptionBase):
    CV = "resume"
