from fastapi import APIRouter, HTTPException, status

from .schemas import BookingCreate, BookingResponse
from .db_connection import get_connection
from .flight_client import get_flight, reserve_seats

booking_router = APIRouter(prefix="/bookings", tags=["Bookings"])


@booking_router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED
)
def create_booking(booking: BookingCreate):
    try:
        flight = get_flight(booking.flight_id)
        if not flight:
            raise HTTPException(404, "Рейс не найден")

        ok, error = reserve_seats(booking.flight_id, booking.seats)
        if not ok:
            raise HTTPException(400, error)

        total_price = flight["price"] * booking.seats

        sql = """
            INSERT INTO "Bookings" (
                "FlightID",
                "PassengerName",
                "Seats",
                "Price"
            )
            VALUES (%s, %s, %s, %s)
            RETURNING "ID";
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        booking.flight_id,
                        booking.passenger_name,
                        booking.seats,
                        total_price
                    )
                )
                booking_id = cur.fetchone()[0]

        return BookingResponse(
            id=booking_id,
            price=total_price,
            **booking.dict()
        )

    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(500, str(ex))
