import ipaddress

from models.ip_ranges import IPRangesModel


class Lookup:
    def __init__(self, ip_ranges_model: IPRangesModel):
        self.ip_ranges_model = ip_ranges_model

    def search(self, ip: str) -> dict:
        ip_int = int(ipaddress.ip_address(ip))
        matches = self.ip_ranges_model.find_by_ip(ip_int)
        return {
            "ip": ip,
            "matched": bool(matches),
            "matches": [
                {
                    "provider": r["provider"],
                    "cidr": r["cidr"],
                    "source": r["source"],
                    "region": r["region"],
                    "service": r["service"],
                    "last_fetched_at": r["fetched_at"],
                }
                for r in matches
            ],
        }
