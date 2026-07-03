import ipaddress

from models.ip_ranges import IPRangesModel


class Lookup:
    def __init__(self, ip_ranges_model: IPRangesModel):
        """
        Args:
            ip_ranges_model: IPRangesModel class used for DB queries.
        """
        self.ip_ranges_model = ip_ranges_model

    def search(self, ip: str) -> dict:
        """
        Check whether an IPv4 address falls within any stored CIDR range.

        Args:
            ip: IPv4 address string (e.g. "104.16.10.20").
        Returns:
            Dict with keys `ip`, `matched` (bool), and `matches` (list of
            provider/cidr/source/region/service/last_fetched_at per match).
        """
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
