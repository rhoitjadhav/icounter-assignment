import json
from unittest.mock import MagicMock, patch

from providers.azure import AzureProvider


class TestAzureProvider:
    def _mock_response(self, body: bytes) -> MagicMock:
        mock = MagicMock()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        mock.read.return_value = body
        return mock

    def test_fetch_returns_decoded_string(self):
        payload = b'{"values": []}'
        provider = AzureProvider()

        with patch.object(provider, "get_url", return_value="http://fake-url"):
            with patch("urllib.request.urlopen", return_value=self._mock_response(payload)):
                result = provider.fetch()

        assert result == '{"values": []}'

    def test_parse_extracts_ipv4_prefixes(self):
        raw = json.dumps({
            "values": [{
                "properties": {
                    "region": "eastus",
                    "systemService": "AzureSQL",
                    "addressPrefixes": ["13.64.0.0/11", "2603:1010::/46"],
                }
            }]
        })
        records = AzureProvider().parse(raw)

        assert len(records) == 1
        assert records[0]["cidr"] == "13.64.0.0/11"
        assert records[0]["provider"] == "Azure"
        assert records[0]["region"] == "eastus"
        assert records[0]["service"] == "AzureSQL"

    def test_parse_skips_ipv6(self):
        raw = json.dumps({
            "values": [{"properties": {"addressPrefixes": ["2603:1010::/46"]}}]
        })
        assert AzureProvider().parse(raw) == []
