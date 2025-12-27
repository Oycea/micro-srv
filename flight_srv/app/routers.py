from fastapi import APIRouter, HTTPException, status, Query
from uuid import UUID
from datetime import date, datetime
from typing import List

from .db_connection import get_connection
from .schemas import (
    FlightCreate,
    FlightResponse,
    FlightInfoResponse
)

flight_router = APIRouter(prefix="/flights", tags=["Flights"])


@flight_router.post(
    "/",
    response_model=FlightResponse,
    status_code=status.HTTP_201_CREATED
)
def create_flight(flight: FlightCreate):
    try:
        sql = """
            INSERT INTO "Flights" (
                "FlightNumber",
                "Origin",
                "Destination",
                "DepartureDate",
                "DepartureTime",
                "AvailableSeats",
                "Price",
                "SeatMap"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING "ID";
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        flight.flight_number,
                        flight.origin,
                        flight.destination,
                        flight.departure_date,
                        flight.departure_time,
                        flight.available_seats,
                        flight.price,
                        flight.seat_map.dict()
                    )
                )
                flight_id = cur.fetchone()[0]

        return FlightResponse(id=flight_id, **flight.dict())

    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(500, str(ex))


@flight_router.post(
    "/{flight_id}/reserve"
)
def reserve_seats(flight_id: UUID, seats: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT "AvailableSeats" FROM "Flights" WHERE "ID" = %s FOR UPDATE;',
                    (flight_id,)
                )
                row = cur.fetchone()

                if not row:
                    raise HTTPException(404, "Рейс не найден")

                if row[0] < seats:
                    raise HTTPException(400, "Недостаточно мест")

                cur.execute(
                    'UPDATE "Flights" SET "AvailableSeats" = "AvailableSeats" - %s WHERE "ID" = %s;',
                    (seats, flight_id)
                )

        return {"status": "reserved"}

    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(500, str(ex))


@flight_router.get(
    "/{flight_id}",
    response_model=FlightResponse
)
def get_flight(flight_id: UUID):
    try:
        sql = """
            SELECT
                "ID",
                "FlightNumber",
                "Origin",
                "Destination",
                "DepartureDate",
                "DepartureTime",
                "AvailableSeats",
                "Price"
            FROM "Flights"
            WHERE "ID" = %s;
        """

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (flight_id,))
                row = cur.fetchone()

        if not row:
            raise HTTPException(404, "Рейс не найден")

        return FlightResponse(
            id=row[0],
            flight_number=row[1],
            origin=row[2],
            destination=row[3],
            departure_date=row[4],
            departure_time=row[5],
            available_seats=row[6],
            price=row[7]
        )

    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(500, str(ex))


@flight_router.get("/info", response_model=FlightInfoResponse,
                   name="Получение информации о рейсе"
)
def get_flight_info(flight_no: str = Query(...),
                    departure_local_date_time: datetime = Query(...)):
    """
    Получить информацию о конкретном рейсе
    по номеру рейса и локальной дате/времени вылета
    """
    try:
        sql_query = """
            SELECT
                "ID",
                "FlightNumber",
                "DepartureTime"
            FROM "Flights"
            WHERE "FlightNumber" = %s
              AND "DepartureTime" = %s;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql_query,
                    (flight_no, departure_local_date_time)
                )
                row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Рейс не найден"
            )

        return {
            "id": row[0],
            "flight_number": row[1],
            "departure_time": row[2]
        }
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера {str(ex)}"
        )


@flight_router.get("/{flight_id}/seat-map", name="Получение схемы мест")
def get_seat_map(flight_id: str):
    """
    Возвращает схему мест на рейсе
    """
    try:
        sql_query = """
            SELECT "SeatMap"
            FROM "Flights"
            WHERE "ID" = %s;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query, (flight_id,))
                row = cur.fetchone()

        if not row or not row[0]:
            raise HTTPException(
                status_code=404,
                detail="Схема мест не найдена"
            )

        return row[0]
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера {str(ex)}"
        )


@flight_router.get(
    "/{flight_id}/reserved-seats",
    name="Получить список занятых мест"
)
def get_reserved_seats(flight_id: str):
    """
    Возвращает список номеров занятых мест на рейсе
    """
    try:
        sql_query = """
            SELECT "SeatMap"
            FROM "Flights"
            WHERE "ID" = %s;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query, (flight_id,))
                row = cur.fetchone()

        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Рейс не найден")

        seat_map = row[0]

        # Собираем только занятые места
        reserved_seats = [
            seat["seat"]
            for seat in seat_map["seats"]
            if seat["available"] is False
        ]

        return reserved_seats

    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера {str(ex)}"
        )
