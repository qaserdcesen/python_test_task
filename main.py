import os
import requests
import psycopg2
from dotenv import load_dotenv
import datetime

"""
MIN_LAT = 40.0
MAX_LAT = 46.0
MIN_LON = 24.0
MAX_LON = 42.0

Требуемое в задании условие - сбор информации о полетах над
Черным морем - в комментарии. В настоящее время
интенсивность гражданских полетов над акваторией Черного
моря довольно низкая, а также имеются ограничения 
бесплатного API. Поэтому для повышения наглядности
датасета область сбора данных была расширена - включены
полеты над Европой.
"""

MIN_LAT, MAX_LAT = 39.0, 55.0
MIN_LON, MAX_LON = 4.0, 42.0


def fetch_active_flights(access_key, limit_per_page=100, max_pages=3):
    all_flights = []
    base_url = "http://api.aviationstack.com/v1/flights"
    for page_index in range(max_pages):
        params = {
            'access_key': access_key,
            'limit': limit_per_page,
            'offset': page_index * limit_per_page,
            'flight_status': 'active'
        }
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json().get('data', [])
        if not data:
            break
        all_flights.extend(data)
    return all_flights


def in_black_sea_bbox(latitude, longitude):
    return (MIN_LAT <= latitude <= MAX_LAT) and (MIN_LON <= longitude <= MAX_LON)


def extract_flight_info(flight):
    dep = flight.get('departure', {})
    arr = flight.get('arrival', {})
    flt = flight.get('flight', {})
    ac = flight.get('aircraft', {})
    al = flight.get('airline', {})
    return {
        'callsign': flt.get('number'),
        'icao_code': flt.get('icao'),
        'aircraft_model': ac.get('icao') or ac.get('iata') or "",
        'airline_name': al.get('name'),
        'departure_airport': dep.get('airport'),
        'departure_iata': dep.get('iata'),
        'departure_icao': dep.get('icao'),
        'arrival_airport': arr.get('airport'),
        'arrival_iata': arr.get('iata'),
        'arrival_icao': arr.get('icao'),
    }


def save_to_db(flights_data):
    if not flights_data:
        print("Нет данных для сохранения в БД.")
        return

    db_host = os.getenv("POSTGRES_HOST", "db")
    db_name = os.getenv("POSTGRES_DB", "flights_db")
    db_user = os.getenv("POSTGRES_USER", "user")
    db_password = os.getenv("POSTGRES_PASSWORD", "password")
    db_port = os.getenv("POSTGRES_PORT", 5432)

    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password
    )
    cur = conn.cursor()

    insert_query = """
        INSERT INTO flights (
            callsign,
            icao_code,
            aircraft_model,
            airline_name,
            departure_airport,
            departure_iata,
            departure_icao,
            arrival_airport,
            arrival_iata,
            arrival_icao,
            collected_at
        )
        VALUES (
            %(callsign)s,
            %(icao_code)s,
            %(aircraft_model)s,
            %(airline_name)s,
            %(departure_airport)s,
            %(departure_iata)s,
            %(departure_icao)s,
            %(arrival_airport)s,
            %(arrival_iata)s,
            %(arrival_icao)s,
            %(collected_at)s
        );
    """

    for flight in flights_data:
        cur.execute(insert_query, flight)

    conn.commit()
    cur.close()
    conn.close()
    print(f"Сохранено {len(flights_data)} рейсов в БД.")


def main():
    load_dotenv()
    access_key = os.getenv("API_KEY")
    if not access_key:
        print("Не найден API_KEY")
        return

    flights = fetch_active_flights(access_key)
    print("Получено рейсов от API:", len(flights))

    filtered = []
    for flight in flights:
        live = flight.get('live', {})
        if live and live.get('latitude') and live.get('longitude'):
            if in_black_sea_bbox(live['latitude'], live['longitude']):
                filtered.append(flight)
    print("Рейсов после фильтрации:", len(filtered))

    final_flights = [extract_flight_info(f) for f in filtered]
    print("Рейсов после обработки:", len(final_flights))

    now_ts = datetime.datetime.utcnow()
    for flight in final_flights:
        flight["collected_at"] = now_ts

    save_to_db(final_flights)


if __name__ == "__main__":
    main()
