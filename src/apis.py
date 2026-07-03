from fastapi import APIRouter, HTTPException, Response

from constants import PROVIDERS
from models.ip_ranges import IPRangesModel
from services.lookup import Lookup
from services.refresh import Refresh

router = APIRouter()


@router.post("/refresh", summary="Refresh IP ranges", tags=["Data"])
async def refresh():
    """
    Fetch and store the latest IP ranges from all configured providers.

    - Runs all providers independently — one failure does not block others.
    - Upserts records: duplicate CIDRs update `fetched_at` only.
    - Returns per-provider success status and number of ranges loaded.
    """
    return Refresh(PROVIDERS).run()


@router.get("/lookup", summary="Lookup an IP address", tags=["Lookup"])
async def lookup(ip: str):
    """
    Check whether an IPv4 address belongs to a known Cloud/CDN/WAF provider.

    - Returns all matching providers if the IP falls within multiple ranges.
    - Returns `matched: false` with empty list if no match found.
    - Returns HTTP 400 if the IP address is invalid.
    """
    try:
        return Lookup(IPRangesModel).search(ip)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid IP address: {ip!r}")


@router.get("/providers", summary="List providers", tags=["Data"])
async def list_providers() -> list:
    """
    List all providers currently stored in the database with their range counts.
    """
    return IPRangesModel.get_provider_counts()


@router.get("/health", summary="Health check", tags=["System"])
async def health():
    """
    Returns service status, total number of stored IP ranges,
    last refresh timestamp, and list of active providers.
    """
    return IPRangesModel.get_health_stats()
