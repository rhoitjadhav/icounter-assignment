from abc import ABC, abstractmethod


class BaseProvider(ABC):
    name: str
    url: str

    @abstractmethod
    def fetch(self) -> str:
        """Fetch raw data from provider URL."""
        ...

    @abstractmethod
    def parse(self, raw: str) -> list[dict]:
        """Parse raw response into list of normalized IP range records."""
        ...

    @abstractmethod
    def normalize(self, cidr: str, **kwargs) -> dict:
        """Convert CIDR + metadata into a DB-ready record dict."""
        ...
