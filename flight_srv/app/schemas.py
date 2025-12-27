from pydantic import BaseModel
from datetime import date, datetime
from uuid import UUID
from typing import List


class Seat(BaseModel):
    seat: str
    available: bool


class SeatMap(BaseModel):
    seats: List[Seat]


class SeatsRequest(BaseModel):
    seats_to_book: List[str]


class FlightBase(BaseModel):
    flight_number: str
    origin: str
    destination: str
    departure_date: date
    departure_time: datetime
    available_seats: int
    price: float


class FlightCreate(FlightBase):
    seat_map: SeatMap


class FlightResponse(FlightBase):
    id: UUID
