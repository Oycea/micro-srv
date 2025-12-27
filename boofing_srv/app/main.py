from fastapi import FastAPI

from .booking_routers import booking_router

app = FastAPI(title="Booking Service")
app.include_router(booking_router)
