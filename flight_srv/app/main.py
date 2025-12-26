from fastapi import FastAPI

from .routers import flight_router

app = FastAPI(title="Flight Service")
app.include_router(flight_router)
