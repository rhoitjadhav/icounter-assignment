import json
from unittest.mock import MagicMock, patch

from providers.aws import AWSProvider


class TestAWSProvider:
    def _mock_response(self, body: bytes) -> MagicMock:
        mock = MagicMock()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        mock.read.return_value = body
        return mock

    def test_fetch_returns_decoded_string(self):
        payload = b'{"prefixes": []}'
        with patch("urllib.request.urlopen", return_value=self._mock_response(payload)):
            result = AWSProvider().fetch()

        assert result == '{"prefixes": []}'

    def test_parse_extracts_prefixes(self):
        raw = json.dumps({
            "prefixes": [
                {"ip_prefix": "3.2.34.0/26", "region": "us-east-1", "service": "AMAZON"},
                {"ip_prefix": "52.93.0.0/16", "region": "eu-west-1", "service": "EC2"},
            ]
        })
        records = AWSProvider().parse(raw)

        assert len(records) == 2
        assert records[0]["cidr"] == "3.2.34.0/26"
        assert records[0]["provider"] == "AWS"
        assert records[0]["region"] == "us-east-1"
        assert records[0]["service"] == "AMAZON"

    def test_parse_empty_prefixes(self):
        raw = json.dumps({"prefixes": []})
        assert AWSProvider().parse(raw) == []
