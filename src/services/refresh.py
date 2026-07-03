import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.ip_ranges import IPRangesModel

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


class Refresh:
    def __init__(self, providers):
        """
        Args:
            providers: list of BaseProvider subclasses to fetch from.
        """
        self.providers = providers

    @staticmethod
    def process_provider(provider_cls) -> tuple:
        """
        Fetch, parse, and store IP ranges for a single provider.
        Args:
            provider_cls: BaseProvider subclass to instantiate and process.

        Returns:
            Tuple of (provider_name, result_dict) where result_dict contains
            `success`, `ranges_loaded` on success or `success`, `error` on failure.
        """
        provider = provider_cls()
        try:
            raw = provider.fetch()
            records = provider.parse(raw)

            for offset in range(0, len(records), BATCH_SIZE):
                IPRangesModel.upsert_many(records[offset:offset + BATCH_SIZE])

            return provider.name, {
                "success": True,
                "ranges_loaded": len(records),
            }
        except Exception as e:
            logger.exception(f"Failed to process {provider.name}")
            return provider.name, {"success": False, "error": str(e)}

    def run(self) -> dict:
        """
        Run refresh for all providers in parallel using ThreadPoolExecutor.
        Returns:
            Dict keyed by provider name with per-provider success/failure result.
        """
        results = {}

        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            futures = {
                executor.submit(self.process_provider, provider_cls): provider_cls
                for provider_cls in self.providers
            }

            for future in as_completed(futures):
                name, result = future.result()
                results[name] = result

        return results
