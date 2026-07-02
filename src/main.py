# Packages
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apis import router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)

app.include_router(router)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8001)
