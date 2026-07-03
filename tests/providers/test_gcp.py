import json
from unittest.mock import MagicMock, patch

from providers.gcp import GCPProvider


class TestGCPProvider:
    def _mock_response(self, body: bytes) -> MagicMock:
        mock = MagicMock()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        mock.read.return_value = body
        return mock

    def test_fetch_returns_decoded_string(self):
        payload = b'{"prefixes": []}'
        with patch("urllib.request.urlopen", return_value=self._mock_response(payload)):
            result = GCPProvider().fetch()

        assert result == '{"prefixes": []}'

    def test_parse_extracts_ipv4_prefixes(self):
        raw = json.dumps({
            "prefixes": [
                {"ipv4Prefix": "34.64.0.0/10", "scope": "asia-east1", "service": "Google Cloud"},
                {"ipv6Prefix": "2600:1900::/28", "scope": "global"},
            ]
        })
        records = GCPProvider().parse(raw)

        assert len(records) == 1
        assert records[0]["cidr"] == "34.64.0.0/10"
        assert records[0]["provider"] == "GCP"
        assert records[0]["region"] == "asia-east1"

    def test_parse_skips_ipv6_only_entries(self):
        raw = json.dumps({
            "prefixes": [{"ipv6Prefix": "2600:1900::/28", "scope": "global"}]
        })
        assert GCPProvider().parse(raw) == []
