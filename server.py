#!/usr/bin/env python3
"""server.py — FastAPI + StaticFiles para jacket-masters.

Sirve el sitio estático (index.html, css, js, img) y expone el contrato REST:
    GET  /api/product    -> tallas, colores, precios y SKUs del puffer
    POST /api/newsletter -> suscripción del footer (valida + guarda en DB)

Listo para desplegar en Render / Railway / Dockerfile:
    * en local, STATIC_DIR apunta a la carpeta donde vive este server.py
      (cualquier copia de la app en el disco);
    * en el contenedor, /app es la carpeta del proyecto y STATIC_DIR = /app.

La variable PORT se lee de entorno (Render / Railway la asignan).
"""

import os
import re
import sqlite3
from contextlib import closing

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, EmailStr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # web/jacket-masters/ (donde vive server.py)
DB_PATH = os.path.join(BASE_DIR, "db", "jacket-masters.db")     # web/jacket-masters/db/

# El sitio estático vive junto a server.py. Funciona tanto en local
# (copias de la app en el disco) como en el contenedor (la app está en /app).
STATIC_DIR = BASE_DIR

app = FastAPI(title="Jacket Masters API")


# ----------conexión a SQLite (one-per-request)-------------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ----------modelos de entrada / salida--------------------------------------
class NewsletterRequest(BaseModel):
    # Usamos str (no EmailStr): la validación la hace nuestra regex
    # (devuelve 400 en vez de 422 de pydantic).
    email: str


class ProductResponse(BaseModel):
    product: dict
    variants: list[dict]
    images: list[dict]


# ----------API de producto (registered BEFORE the static wildcard)-------
@app.get("/api/product", response_model=ProductResponse)
def get_product():
    conn = get_conn()
    try:
        prod = conn.execute(
            "SELECT id, handle, name, tagline, sku, original_price, sale_price, description "
            "FROM products WHERE status='active' ORDER BY id LIMIT 1"
        ).fetchone()

        variants = conn.execute(
            "SELECT size, color, color_hex, sku, stock FROM variants WHERE product_id=? ORDER BY size",
            (prod["id"],),
        ).fetchall()

        images = conn.execute(
            "SELECT url, alt FROM images WHERE product_id=? ORDER BY sort_order",
            (prod["id"],),
        ).fetchall()

        if not prod:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        return {
            "product": {
                "id": prod["id"],
                "handle": prod["handle"],
                "name": prod["name"],
                "tagline": prod["tagline"],
                "sku": prod["sku"],
                "original_price": prod["original_price"],
                "sale_price": prod["sale_price"],
                "sale_flag": bool(prod["sale_price"]) and prod["original_price"] != prod["sale_price"],
                "description": prod["description"],
            },
            "variants": [
                {"size": v["size"], "color": v["color"], "color_hex": v["color_hex"],
                 "sku": v["sku"], "stock": v["stock"]}
                for v in variants
            ],
            "images": [{"url": i["url"], "alt": i["alt"]} for i in images],
        }
    finally:
        conn.close()


# ----------API de newsletter-------------------------------------------------
@app.post("/api/newsletter")
def newsletter(payload: NewsletterRequest):
    email = payload.email.lower().strip()
    if not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email):
        raise HTTPException(status_code=400, detail="Correo no válido")

    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT id, status FROM newsletter_subscribers WHERE email=? LIMIT 1",
            (email,),
        ).fetchone()
        if existing:
            # Ya existe (pending o confirmed): rechazar con 409 para
            # respetar el contrato del backend y evitar doble suscripción.
            raise HTTPException(status_code=409, detail="Ya estás suscrito")
        conn.execute(
            "INSERT INTO newsletter_subscribers (email, status) VALUES (?, 'pending')", (email,),
        )
        conn.commit()
    finally:
        conn.close()

    # En producción enviar confirmación por correo aquí (SMTP); la token
    # de verificación se genera en el backend y se guarda en otro tablón.
    return {"accepted": True, "email": email, "status": "pending_confirmation"}


@app.get("/api/newsletter")
def newsletter_get():
    # Solo POST; cualquier otro método devuelve 405.
    raise HTTPException(status_code=405, detail="Method not allowed")


# ----------rutas del sitio estático------------------------------------------
# REGISTER AFTER the API routes: the wildcard below must NOT shadow /api/*
@app.get("/")
@app.get("/{full_path:path}")
def serve_site(full_path: str = ""):
    """Sirve cualquier archivo estático dentro del proyecto.

    Devolvemos always index.html para que el router del frontend
    maneja las rutas cliente (SPA single-page).
    """
    if full_path in ("", "index.html"):
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    safe = os.path.normpath(full_path).lstrip("/")
    # bloquear acceso a DB, esquema e implementaciones de primer nivel
    if safe.startswith(("schema", "db", "init_db")) or safe.endswith((".pyc", ".pyo", "~")):
        raise HTTPException(status_code=403, detail="Forbidden")

    target = os.path.join(STATIC_DIR, safe)
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="Not found")

    ext = os.path.splitext(target)[1].lower()
    ctype = {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
    }.get(ext, "application/octet-stream")
    return FileResponse(target, media_type=ctype)


# ----------punto de entrada para Render / Railway----------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
