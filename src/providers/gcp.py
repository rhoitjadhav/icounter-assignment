import ipaddress
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone

from tenacity import retry, stop_after_attempt

import config
from providers.base import BaseProvider


class GCPProvider(BaseProvider):
    name = "GCP"
    url = config.GCP_URL

    @retry(stop=stop_after_attempt(3))
    def fetch(self) -> str:
        with urllib.request.urlopen(self.url, timeout=30) as response:
            return response.read().decode("utf-8")

    def parse(self, raw: str) -> list[dict]:
        data = json.loads(raw)
        return [
            self.normalize(
                cidr=prefix["ipv4Prefix"],
                region=prefix.get("scope"),
                service=prefix.get("service"),
            )
            for prefix in data.get("prefixes", [])
            if "ipv4Prefix" in prefix
        ]

    def normalize(self, cidr: str, **kwargs) -> dict:
        network = ipaddress.ip_network(cidr, strict=False)
        return {
            "cidr": str(network),
            "provider": self.name,
            "source": self.name.lower(),
            "ip_version": network.version,
            "network_int": int(network.network_address),
            "broadcast_int": int(network.broadcast_address),
            "region": kwargs.get("region"),
            "service": kwargs.get("service"),
            "fetched_at": datetime.now(timezone.utc),
        }
