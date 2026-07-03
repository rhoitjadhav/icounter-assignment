from unittest.mock import MagicMock, patch

from providers.cloudflare import CloudflareProvider


class TestCloudflareProvider:
    def _mock_response(self, body: bytes) -> MagicMock:
        mock = MagicMock()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        mock.read.return_value = body
        return mock

    def test_fetch_returns_decoded_string(self):
        payload = b"103.21.244.0/22\n103.22.200.0/22\n"
        with patch(
            "urllib.request.urlopen", return_value=self._mock_response(payload)
        ):
            result = CloudflareProvider().fetch()

        assert result == "103.21.244.0/22\n103.22.200.0/22\n"

    def test_parse_extracts_cidrs(self):
        raw = "103.21.244.0/22\n103.22.200.0/22\n"
        records = CloudflareProvider().parse(raw)

        assert len(records) == 2
        assert records[0]["cidr"] == "103.21.244.0/22"
        assert records[0]["provider"] == "Cloudflare"
        assert records[0]["region"] is None
        assert records[0]["service"] is None

    def test_parse_skips_blank_and_html_lines(self):
        raw = "\n<html>\n103.21.244.0/22\n"
        records = CloudflareProvider().parse(raw)

        assert len(records) == 1
        assert records[0]["cidr"] == "103.21.244.0/22"
