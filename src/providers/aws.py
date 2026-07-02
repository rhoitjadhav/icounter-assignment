import urllib.error
import urllib.request

from tenacity import retry, stop_after_attempt

from providers.base import BaseProvider


class AWSProvider(BaseProvider):
    name = "AWS"
    url = "https://ip-ranges.amazonaws.com/ip-ranges.json"

    @retry(stop=stop_after_attempt(3))
    def fetch(self) -> str:
        with urllib.request.urlopen(self.url, timeout=30) as response:
            return response.read().decode("utf-8")

    def parse(self, raw: str) -> list[dict]:
        """Parse raw response into list of normalized IP range records."""
        ...

    def normalize(self, cidr: str, **kwargs) -> dict:
        """Convert CIDR + metadata into a DB-ready record dict."""
        ...
