from abc import ABC, abstractmethod


class ApiClient(ABC):
    @abstractmethod
    def get_data(self):
        pass
