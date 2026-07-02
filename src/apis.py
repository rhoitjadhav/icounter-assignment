from fastapi import APIRouter, HTTPException, Response

from constants import PROVIDERS
from models.ip_ranges import IPRangesModel
from services.lookup import Lookup
from services.refresh import Refresh

router = APIRouter()


@router.post("/refresh")
async def refresh():
    return Refresh(PROVIDERS).run()


@router.get("/lookup")
async def lookup(ip: str):
    try:
        return Lookup(IPRangesModel).search(ip)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid IP address: {ip!r}")


@router.get("/providers")
async def list_providers() -> list:
    return IPRangesModel.get_provider_counts()


@router.get("/health")
async def health():
    return IPRangesModel.get_health_stats()
