import ipaddress
import urllib.error
import urllib.request
from datetime import datetime, timezone

from tenacity import retry, stop_after_attempt

import config
from providers.base import BaseProvider


class CloudflareProvider(BaseProvider):
    name = "Cloudflare"
    url = config.CLOUDFLARE_URL

    @retry(stop=stop_after_attempt(3))
    def fetch(self) -> str:
        req = urllib.request.Request(
            self.url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")

    def parse(self, raw: str) -> list[dict]:
        records = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("<"):
                continue
            try:
                records.append(self.normalize(cidr=line))
            except ValueError:
                continue
        return records

    def normalize(self, cidr: str, **kwargs) -> dict:
        network = ipaddress.ip_network(cidr, strict=False)
        return {
            "cidr": str(network),
            "provider": self.name,
            "source": self.name.lower(),
            "ip_version": network.version,
            "network_int": int(network.network_address),
            "broadcast_int": int(network.broadcast_address),
            "region": None,
            "service": None,
            "fetched_at": datetime.now(timezone.utc),
        }
