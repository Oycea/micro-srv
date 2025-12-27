from pydantic import BaseModel
from uuid import UUID


class BookingCreate(BaseModel):
    flight_id: UUID
    passenger_name: str
    seats: int


class BookingResponse(BookingCreate):
    id: UUID
    price: float
