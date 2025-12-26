from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import date

from .db_connection import get_connection
from .schemas import FlightCreate, FlightResponse


flight_router = APIRouter(prefix='/flights', tags=['Flights'])


@flight_router.post('/', status_code=status.HTTP_200_OK,
                    response_model=FlightResponse,
                    name="Создание рейса")
def create_flight(flight: FlightCreate):
    """
    Создание нового рейса
    :param flight: Данные рейса в формате JSON
    :return: ID рейса
    """
    try:
        sql_query = """
                    INSERT INTO "Flights" (
                        "FlightNumber",
                        "Origin",
                        "Destination",
                        "DepartureDate",
                        "AvailableSeats",
                        "Price"
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING "ID";
                    """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql_query,
                    (
                        flight.flight_number,
                        flight.origin,
                        flight.destination,
                        flight.departure_date,
                        flight.available_seats,
                        flight.price,
                    ),
                )
                flight_id = cur.fetchone()[0]
                return FlightResponse(id=flight_id, **flight.dict())
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера {str(ex)}"
        )


@flight_router.get("/search", response_model=List[FlightResponse])
def search_flights(origin: str, destination: str, departure_date: date):
    """
    Поиск рейсов по маршруту и дате
    """
    try:
        sql_query = """
                    SELECT
                        "ID",
                        "FlightNumber",
                        "Origin",
                        "Destination",
                        "DepartureDate",
                        "AvailableSeats",
                        "Price"
                    FROM "Flights"
                    WHERE "Origin" = %s
                        AND "Destination" = %s
                        AND "DepartureDate" = %s
                        AND "AvailableSeats" > 0;
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql_query,
                    (
                        origin,
                        destination,
                        departure_date
                    )
                )
                rows = cur.fetchall()

        # Преобразуем строки из БД в список объектов FlightResponse
        flights = []
        for row in rows:
            flights.append(
                FlightResponse(
                    id=row[0],
                    flight_number=row[1],
                    origin=row[2],
                    destination=row[3],
                    departure_date=row[4],
                    available_seats=row[5],
                    price=row[6],
                )
            )
        return flights
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера {str(ex)}"
        )
