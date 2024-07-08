from abc import abstractmethod


class BasePopulator:
    @abstractmethod
    def populate(self) -> None:
        pass
