from datetime import datetime, timezone
import ipaddress
import json
import urllib.request

from tenacity import retry, stop_after_attempt

import config
from providers.base import BaseProvider

"""
{
  "addresses": [
    "23.235.32.0/20",
    "43.249.72.0/22",
    "103.244.50.0/24",
    "103.245.222.0/23",
    "103.245.224.0/24",
    "104.156.80.0/20",
    "140.248.64.0/18",
    "140.248.128.0/17",
    "146.75.0.0/17",
    "151.101.0.0/16",
    "157.52.64.0/18",
    "167.82.0.0/17",
    "167.82.128.0/20",
    "167.82.160.0/20",
    "167.82.224.0/20",
    "172.111.64.0/18",
    "185.31.16.0/22",
    "199.27.72.0/21",
    "199.232.0.0/16"
  ],
  "ipv6_addresses": [
    "2a04:4e40::/32",
    "2a04:4e42::/32"
  ]
}
"""


class FastlyProvider(BaseProvider):
    name = "Fastly"
    url = config.FASTLY_URL

    @retry(stop=stop_after_attempt(3))
    def fetch(self) -> list[dict]:
        with urllib.request.urlopen(self.url) as response:
            return response.read().decode("utf-8")

    def parse(self, raw: str):
        data = json.loads(raw)
        return [
            self.normalize(address) for address in data.get("addresses", [])
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
