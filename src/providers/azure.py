import ipaddress
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from tenacity import retry, stop_after_attempt

import config
from providers.base import BaseProvider


class AzureProvider(BaseProvider):
    name = "Azure"
    url = config.AZURE_URL

    def get_url(self) -> str:
        today = datetime.now(timezone.utc).date()
        last_monday = today - timedelta(days=today.weekday())
        for weeks_back in range(3):
            date = (last_monday - timedelta(weeks=weeks_back)).strftime("%Y%m%d")
            url = self.url.format(date=date)
            try:
                urllib.request.urlopen(url, timeout=10).close()
                return url
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise
        raise RuntimeError("Azure: no published file found for last 3 Mondays")

    @retry(stop=stop_after_attempt(3))
    def fetch(self) -> str:
        url = self.get_url()
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode("utf-8")

    def parse(self, raw: str) -> list[dict]:
        data = json.loads(raw)
        records = []
        for entry in data.get("values", []):
            props = entry.get("properties", {})
            region = props.get("region") or None
            service = props.get("systemService") or None
            for cidr in props.get("addressPrefixes", []):
                if ":" in cidr:
                    continue
                records.append(self.normalize(cidr=cidr, region=region, service=service))
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
            "region": kwargs.get("region"),
            "service": kwargs.get("service"),
            "fetched_at": datetime.now(timezone.utc),
        }
