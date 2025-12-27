from fastapi import APIRouter, HTTPException, status, Path

import os
from .schemas import BookingCreate, BookingResponse
from .db_connection import get_connection
from .flight_client import get_flight, reserve_seats

import requests

booking_router = APIRouter(prefix="/bookings", tags=["Bookings"])
FLIGHT_SERVICE_URL = os.getenv("FLIGHT_SERVICE_URL")


@booking_router.get(
    "/{flight_id}/free-seats",
    name="Получить список свободных мест"
)
def get_free_seats(flight_id: str = Path(..., description="ID рейса")):
    """
    Возвращает список занятых мест на рейсе
    """
    try:
        url = f"{FLIGHT_SERVICE_URL}/flights/{flight_id}/free-seats"
        r = requests.get(url, timeout=5)
        if r.status_code == 404:
            raise HTTPException(404, "Рейс не найден")
        elif r.status_code != 200:
            raise HTTPException(r.status_code, f"Ошибка рейсового сервиса: {r.text}")

        return r.json()  # Список занятых мест

    except requests.exceptions.RequestException as ex:
        raise HTTPException(500, f"Ошибка при подключении к рейсовому сервису: {str(ex)}")


@booking_router.post("/", response_model=BookingResponse,
                     status_code=status.HTTP_201_CREATED,
                     name="Забронировать место на рейсе")
def create_booking(booking: BookingCreate):
    try:
        # Проверка существования рейса
        r = requests.get(f"{FLIGHT_SERVICE_URL}/flights/{booking.flight_id}")
        if r.status_code == 404:
            raise HTTPException(404, "Рейс не найден")
        elif r.status_code != 200:
            raise HTTPException(r.status_code,
                                f"Ошибка сервиса рейсов: {r.text}")
        flight = r.json()

        # Бронь места через сервис рейсов
        r2 = requests.post(
            f"{FLIGHT_SERVICE_URL}/flights/{booking.flight_id}/reserve",
            json={"seats_to_book": booking.seats}
        )
        if r2.status_code != 200:
            raise HTTPException(r2.status_code, r2.json().get("detail",
                                                              "Не удалось забронировать места"))

        # Подсчёт стоимости билетов
        total_price = flight["price"] * len(booking.seats)

        # Сохранение брони
        sql = """
                INSERT INTO "Bookings" ("FlightID", "PassengerName", "Seats", "Price")
                VALUES (%s, %s, %s, %s)
                RETURNING "ID";
                """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    str(booking.flight_id),
                    booking.passenger_name,
                    booking.seats,
                    total_price
                ))
                booking_id = cur.fetchone()[0]
        return BookingResponse(id=booking_id, price=total_price, **booking.dict())
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(500, f"Ошибка при бронировании: {str(ex)}")
