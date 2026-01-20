# Sports Magazine SaaS — v10.3.1 (local)

## Requisitos
- Docker + Docker Compose (recomendado en WSL)
- Node 18+ (solo si quieres correr frontend sin Docker)

## Arranque (recomendado)
Desde la carpeta del proyecto:

```bash
docker compose down -v
docker compose up --build
```

> Importante: usamos `docker compose down -v` la primera vez (o tras actualizar) porque el esquema de la BD puede cambiar (por ejemplo `assets.is_catalog`).

## URLs
- Frontend: http://localhost:5173
- Backend (API): http://localhost:8000

## Si ves el error `ECONNREFUSED 127.0.0.1:8000` al registrarte
Eso significa que el backend no está levantado (o el compose no arrancó bien). Revisa:

```bash
docker compose ps
docker compose logs -n 200 backend
```

## Si Docker se queja de puertos Postgres ocupados
En esta versión NO exponemos Postgres al host (para evitar el típico conflicto con 5432/5433).  
Si tú lo has descomentado, vuelve a comentarlo o cambia el puerto.

## Plantillas
- Se generan 20 plantillas nativas (40 páginas) con assets de ejemplo (hero/portrait/sponsors).
- En el dashboard puedes abrir el modal de vista previa (3 páginas) antes de usar.

## Editor
- + Texto, + Imagen, Duplicar página
- Cambiar fondo (si la página tiene fondo detectado: plantillas y PDF import)
- Texto con estilos dentro de una frase: doble click en un cuadro de texto -> editor pro (negrita/cursiva/color/tamaño)

## Importar PDF
- Modo seguro: cada página se rasteriza como fondo + se detectan cajas de texto e imágenes (cuando el PDF lo permite).
- El fondo se gestiona con los botones “Cambiar fondo” / “Seleccionar fondo” para no confundir al usuario.

## Hotfix2 (ECONNRESET / backend caído)
Si el frontend muestra `http proxy error ... ECONNRESET`, es porque el backend se reinicia o no está listo.
Esta versión:
- elimina `pip install` en runtime
- elimina `--reload`
- añade healthchecks y `depends_on: condition: service_healthy`

Arranque recomendado:
```bash
docker compose down -v --remove-orphans
docker compose up --build
curl -i http://localhost:8000/api/health
```


## HOTFIX3 (estabilidad WSL)
- Se ha eliminado el bind-mount `./backend:/app` en Docker para evitar crashes/restarts en WSL.
- Para editar código en vivo, puedes volver a añadir ese volumen en dev.
