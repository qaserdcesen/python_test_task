Запуск контейнеров

сбор образа
```
docker compose build --no-cache
```

запуск проекта
```
docker compose up -d
```

подключение к БД
```
docker exec -it flights_db_container psql -U user -d flights_db
```

внутри psql:
```
\dt
```
```
SELECT COUNT(*) FROM flights;
```
```
SELECT * FROM flights_agg_daily;
```
```
SELECT * FROM flights_agg_hourly;
```
