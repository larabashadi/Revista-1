# Hotfix4: Backend restarting en WSL (driver Postgres)

Si el backend se queda en `Restarting`, suele ser por problemas con `psycopg2` en algunas instalaciones/arquitecturas.
Este hotfix cambia el driver a **psycopg3**:

- Se sustituye `psycopg2-binary` por `psycopg[binary]`
- Se actualiza `DATABASE_URL` a `postgresql+psycopg://...`

## Arranque recomendado
```bash
docker compose down -v --remove-orphans
docker compose up --build
```
Luego:
```bash
curl -i http://localhost:8000/api/health
```
