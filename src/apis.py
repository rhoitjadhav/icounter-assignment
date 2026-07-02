from fastapi import APIRouter, Response


router = APIRouter()


@router.post("/refresh")
def refresh():
    pass


@router.get("/lookup")
def lookup(ip: str):
    pass


@router.get("/providers")
def list_providers() -> list:
    pass


@router.get("/health")
def health():
    pass


