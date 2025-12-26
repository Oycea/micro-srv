from pydantic import BaseModel
from datetime import date
from uuid import UUID


class FlightCreate(BaseModel):
    flight_number: str
    origin: str
    destination: str
    departure_date: date
    available_seats: int
    price: float


class FlightResponse(FlightCreate):
    id: UUID
