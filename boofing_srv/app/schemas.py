from pydantic import BaseModel
from uuid import UUID
from typing import List


class BookingCreate(BaseModel):
    flight_id: UUID
    passenger_name: str
    seats: List[str]


class BookingResponse(BookingCreate):
    id: UUID
    price: float
