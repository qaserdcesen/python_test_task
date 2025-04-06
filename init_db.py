import os
import psycopg2
from dotenv import load_dotenv

def init_db():
    load_dotenv()

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

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS flights (
        id SERIAL PRIMARY KEY,
        callsign VARCHAR(50),
        icao_code VARCHAR(20),
        aircraft_model VARCHAR(50),
        airline_name VARCHAR(100),
        departure_airport VARCHAR(100),
        departure_iata VARCHAR(10),
        departure_icao VARCHAR(10),
        arrival_airport VARCHAR(100),
        arrival_iata VARCHAR(10),
        arrival_icao VARCHAR(10),
        collected_at TIMESTAMP
    );
    """
    cur.execute(create_table_sql)

    alter_sql = """
    ALTER TABLE flights
    ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP;
    """
    cur.execute(alter_sql)

    create_view_daily = """
    CREATE OR REPLACE VIEW flights_agg_daily AS
    SELECT
      date_trunc('day', collected_at) AS day_date,
      aircraft_model,
      airline_name,
      COUNT(*) AS flight_count
    FROM flights
    GROUP BY 1, aircraft_model, airline_name
    ORDER BY day_date DESC, flight_count DESC
    """
    cur.execute(create_view_daily)

    create_view_hourly = """
    CREATE OR REPLACE VIEW flights_agg_hourly AS
    SELECT
      date_trunc('hour', collected_at) AS hour_date,
      aircraft_model,
      airline_name,
      COUNT(*) AS flight_count
    FROM flights
    GROUP BY 1, aircraft_model, airline_name
    ORDER BY hour_date DESC, flight_count DESC
    """
    cur.execute(create_view_hourly)

    conn.commit()
    cur.close()
    conn.close()
    print("Таблица flights, и вьюхи flights_agg_daily/hourly созданы (или обновлены).")

if __name__ == "__main__":
    init_db()
