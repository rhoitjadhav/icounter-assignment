# Packages
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apis import router

app = FastAPI(
    title="IP Lookup Service",
    description="A FastAPI based service that collects public IP ranges from Cloud/CDN/WAF providers and identifies whether a given IP belongs to one of those providers.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
