import json

from fastapi import APIRouter, HTTPException, status, Query
from uuid import UUID

from .db_connection import get_connection
from .schemas import FlightCreate, FlightResponse, SeatsRequest


flight_router = APIRouter(prefix="/flights", tags=["Flights"])


@flight_router.post(
    "/create",
    response_model=FlightResponse,
    status_code=status.HTTP_201_CREATED,
    name="Создать рейс"
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
                        json.dumps(flight.seat_map.dict())
                    )
                )
                flight_id = cur.fetchone()[0]

        return FlightResponse(id=flight_id, **flight.dict())

    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(500, str(ex))


@flight_router.post("/{flight_id}/reserve",
                    name="Забронировать места")
def reserve_seats(flight_id: UUID, request: SeatsRequest):
    """
    Резервирование конкретных мест
    """
    try:
        seats_to_book = request.seats_to_book
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Получаем seat_map с блокировкой
                cur.execute('SELECT "SeatMap", "AvailableSeats" FROM "Flights" WHERE "ID"=%s FOR UPDATE;', (flight_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(404, "Рейс не найден")

                seat_map = row[0]
                available_seats = row[1]

                if len(seats_to_book) > available_seats:
                    raise HTTPException(400, "Недостаточно свободных мест")

                seats = seat_map.get("seats", [])

                # Проверяем, что все выбранные места свободны
                for s in seats_to_book:
                    if not any(seat["seat"] == s and seat["available"] for seat in seats):
                        raise HTTPException(400, f"Место {s} недоступно")

                # Помечаем места как занятые
                for seat in seats:
                    if seat["seat"] in seats_to_book:
                        seat["available"] = False

                # Обновляем БД
                cur.execute(
                    'UPDATE "Flights" SET "SeatMap"=%s, "AvailableSeats"="AvailableSeats"-%s WHERE "ID"=%s;',
                    (json.dumps(seat_map), len(seats_to_book), flight_id)
                )
        return {"status": "reserved", "seats": seats_to_book}
    except Exception as ex:
        raise HTTPException(500, str(ex))


@flight_router.get("/{flight_id}", response_model=FlightResponse,
                   name="Получить информацию о рейсе по его ID")
def get_flight_by_id(flight_id: UUID):
    try:
        sql = """
        SELECT "ID","FlightNumber","Origin","Destination",
               "DepartureDate","DepartureTime","AvailableSeats","Price","SeatMap"
        FROM "Flights" WHERE "ID"=%s;
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (flight_id,))
                row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Рейс не найден")

        return FlightResponse(
            id=row[0], flight_number=row[1], origin=row[2], destination=row[3],
            departure_date=row[4], departure_time=row[5],
            available_seats=row[6], price=row[7], seat_map=row[8]
        )
    except Exception as ex:
        raise HTTPException(500, str(ex))


@flight_router.get("/search", response_model=FlightResponse,
                   name="Получить ID рейса по номеру и дате")
def get_flight_id_by_name_and_date(
        flight_number: str = Query(..., description="Номер рейса"),
        departure_date: str = Query(..., description="Дата отправления в формате YYYY-MM-DD")):
    try:
        sql = """
                   SELECT "ID"
                   FROM "Flights"
                   WHERE "FlightNumber" = %s
                     AND "DepartureDate" = %s
                   LIMIT 1;
               """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (flight_number, departure_date))
                row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Рейс не найден")

        return {"flight_id": row[0]}
    except Exception as ex:
        raise HTTPException(500, str(ex))


@flight_router.get(
    "/{flight_id}/free-seats",
    name="Получить список свободных мест"
)
def get_free_seats(flight_id: str):
    """
    Возвращает список номеров свободных мест на рейсе
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
            if seat["available"] is True
        ]

        return reserved_seats

    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера {str(ex)}"
        )
