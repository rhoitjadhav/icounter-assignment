import logging

from models.ip_ranges import IPRangesModel

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


class Refresh:
    def __init__(self, providers):
        self.providers = providers

    def run(self) -> dict:
        results = {}
        for provider_cls in self.providers:
            provider = provider_cls()
            try:
                raw = provider.fetch()
                records = provider.parse(raw)
                offset = 0
                while offset < len(records):
                    IPRangesModel.upsert_many(records[offset: offset + BATCH_SIZE])
                    offset += BATCH_SIZE
                results[provider.name] = {
                    "success": True,
                    "ranges_loaded": len(records),
                }
                logger.info(f"{provider.name}: loaded {len(records)} ranges")
            except Exception as e:
                results[provider.name] = {"success": False, "error": str(e)}
                logger.exception(f"Failed to refresh {provider.name}")
        return results
