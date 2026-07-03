from unittest.mock import MagicMock, patch

from services.refresh import Refresh


class TestRefresh:
    def _make_provider_cls(self, name, records):
        instance = MagicMock()
        instance.name = name
        instance.fetch.return_value = "raw"
        instance.parse.return_value = records
        return MagicMock(return_value=instance)

    def test_process_provider_success(self):
        cls = self._make_provider_cls("AWS", [{"cidr": "1.2.3.0/24"}] * 3)

        with patch("services.refresh.IPRangesModel.upsert_many"):
            name, result = Refresh.process_provider(cls)

        assert name == "AWS"
        assert result == {"success": True, "ranges_loaded": 3}

    def test_process_provider_fetch_exception(self):
        instance = MagicMock()
        instance.name = "AWS"
        instance.fetch.side_effect = RuntimeError("timeout")
        cls = MagicMock(return_value=instance)

        name, result = Refresh.process_provider(cls)

        assert name == "AWS"
        assert result["success"] is False
        assert "timeout" in result["error"]

    def test_run_returns_results_for_all_providers(self):
        providers = [
            self._make_provider_cls("AWS", [{"cidr": "1.0.0.0/8"}]),
            self._make_provider_cls("GCP", [{"cidr": "2.0.0.0/8"}]),
        ]

        with patch("services.refresh.IPRangesModel.upsert_many"):
            results = Refresh(providers).run()

        assert set(results.keys()) == {"AWS", "GCP"}
        assert results["AWS"]["success"] is True
        assert results["GCP"]["success"] is True
