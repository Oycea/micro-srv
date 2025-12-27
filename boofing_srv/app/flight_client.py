import os
import requests

FLIGHT_SERVICE_URL = os.getenv("FLIGHT_SERVICE_URL")


def get_flight(flight_id):
    r = requests.get(f"{FLIGHT_SERVICE_URL}/flights/{flight_id}")
    if r.status_code != 200:
        return None
    return r.json()


def reserve_seats(flight_id, seats):
    r = requests.post(
        f"{FLIGHT_SERVICE_URL}/flights/{flight_id}/reserve",
        params={"seats": seats}
    )
    if r.status_code != 200:
        return False, r.json().get("detail")
    return True, None
