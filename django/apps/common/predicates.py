from typing import List

import rules


def has_perms(perms: List[str]):
    def predicate(user):
        return user.has_perms(perms)

    return rules.predicate(predicate)
