# Arranque en local (WSL)

## 0) Requisitos
- Docker + Docker Compose
- Node 18+ (recomendado 20)

## 1) Arrancar Backend (API)
Desde la raiz del proyecto:

```bash
docker compose down -v --remove-orphans
docker compose up --build
```

Comprueba:

```bash
curl -s http://localhost:8000/api/health
curl -s http://localhost:8000/api/version
```

## 2) Arrancar Frontend
En otra terminal:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Abre: http://localhost:5173

## 3) Si ves errores tipo ECONNRESET / API
- Mira logs del backend:

```bash
docker compose logs -n 200 -f backend
```

- Asegura que estas usando esta build:

```bash
cat VERSION_BUILD.txt
```

## 4) Passwords
Si usas bcrypt, evita passwords extremadamente largas (72 bytes max). Usa una normal (ej: 10-20 chars).
