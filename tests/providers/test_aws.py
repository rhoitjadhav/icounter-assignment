import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from providers.aws import AWSProvider


class TestAWSProviderFetch:

    @pytest.fixture
    def provider(self):
        return AWSProvider()

    def _mock_response(self, body: bytes) -> MagicMock:
        mock = MagicMock()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        mock.read.return_value = body
        return mock

    def test_fetch_returns_decoded_string(self, provider):
        payload = b'{"prefixes": []}'
        with patch("urllib.request.urlopen", return_value=self._mock_response(payload)):
            result = provider.fetch()
        assert result == '{"prefixes": []}'
