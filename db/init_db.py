#!/usr/bin/env python3
"""init_db.py — crea/impone el esquema y carga los datos del video.

Uso:
    python3 init_db.py [--db PATH] [--seed]

    --seed  inserta el producto Jacket Masters con los datos extraídos del
            video (tallas 36/38/40, colores orange/black/red, $199 -> $149).
            Sin --seed solo se crea la estructura vacía.

Salida:
    - base de datos SQLite listas para conectar a FastAPI
    - impresión de tablas e inserciones realizadas
"""

import argparse
import sqlite3
import sys

BASE_DIR = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
SCHEMA_PATH = __import__("os").path.join(BASE_DIR, "schema.sql")


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def load_schema(conn: sqlite3.Connection) -> None:
    sql = __import__("os").path.join(BASE_DIR, "schema.sql")
    with open(sql, encoding="utf-8") as fh:
        conn.executescript(fh.read())
    conn.commit()


def seed_product(conn: sqlite3.Connection) -> int:
    """Inserta el producto Jacket Masters con las variantes del video."""
    conn.execute(
        """
        INSERT OR IGNORE INTO products (handle, name, tagline, sku, original_price,
                              sale_price, description, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
        """,
        (
            "jacket-masters",
            "Puffer Masters",
            "Stand out Without trying",
            "PM-001",
            19900,      # $199
            14900,      # $149
            "Puffer en naranja, gris y rojo. Tallas 36/38/40. Precio original $199, "
            "con descuento hasta $149.",
            "2026-10-22 00:00:00",
            "2026-10-22 00:00:00",
        ),
    )
    # En caso de que el producto ya exista (re-run de seed), refresco los
    # campos con los datos del video (tallas, colores, precios).
    conn.execute(
        """
        UPDATE products SET name=?, tagline=?, sku=?, original_price=?, sale_price=?, description=?, status=?, updated_at=?
        WHERE handle=?
        """,
        ("Puffer Masters", "Stand out Without trying", "PM-001",
         19900, 14900,
         "Puffer en naranja, gris y rojo. Tallas 36/38/40. Precio original $199, "
         "con descuento hasta $149.",
         "active", "2026-10-22 00:00:00", "jacket-masters"),
    )
    product_id = conn.execute("SELECT id FROM products WHERE handle='jacket-masters'").fetchone()["id"]

    variants = [
        # (size, color, hex, sku)
        (36, "orange",  "#e8a849", "WM-36-ORG"),
        (38, "orange",  "#e8a849", "WM-38-ORG"),
        (40, "orange",  "#e8a849", "WM-40-ORG"),
        (36, "black",   "#0c0c0c", "WM-36-BLK"),
        (38, "black",   "#0c0c0c", "WM-38-BLK"),
        (40, "black",   "#0c0c0c", "WM-40-BLK"),
        (36, "red",     "#c0392b", "WM-36-RED"),
        (38, "red",     "#c0392b", "WM-38-RED"),
        (40, "red",     "#c0392b", "WM-40-RED"),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO variants (product_id, size, color, color_hex, sku, stock)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        [(product_id, size, color, color_hex, sku) for size, color, color_hex, sku in variants],
    )

    # Galería: 4 imágenes del producto (placeholder hasta tener fotos reales)
    images = [
        ("/img/hero.jpg",            "Hero principal del puffer"),
        ("/img/color-swatches.jpg",  "Selector de colores"),
        ("/img/sizes.jpg",           "Ficha técnica con tallas"),
        ("/img/testimonial.jpg",     "Tarjeta de testimonial"),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO images (product_id, sort_order, url, alt)
        VALUES (?, ?, ?, ?)
        """,
        [(product_id, i + 1, url, alt) for i, (url, alt) in enumerate(images)],
    )

    conn.commit()
    return product_id


def dump(conn: sqlite3.Connection) -> None:
    print("\n=== BASE DE DATOS: jacket-masters ===")
    for table in ("products", "variants", "images", "newsletter_subscribers"):
        rows = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        print(f"  {table:<22} {rows} registro(s)")

    prod = conn.execute("SELECT * FROM products WHERE handle='jacket-masters'").fetchone()
    if prod:
        print("\n--- Producto ---")
        for key in ("handle", "name", "tagline", "sku", "original_price", "sale_price"):
            print(f"  {key:<18} {prod[key]}")
        print("  variants:")
        for v in conn.execute("SELECT size, color, color_hex, sku, stock FROM variants WHERE product_id=?",
                              (prod["id"],)).fetchall():
            print(f"    - {v['size']:>2} {v['color']:<7} {v['color_hex']:<8} {v['sku']:<10} stock={v['stock']}")
        print("  images:")
        for im in conn.execute("SELECT url, alt FROM images WHERE product_id=? ORDER BY sort_order", (prod["id"],)).fetchall():
            print(f"    - {im['url']}  ({im['alt']})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inicializa la base de datos de Jacket Masters.")
    parser.add_argument("--db", default="jacket-masters.db", help="Ruta de la base de datos (default: jacket-masters.db)")
    parser.add_argument("--seed", action="store_true", help="Inserta el producto del video")
    args = parser.parse_args()

    if not __import__("os").path.exists(SCHEMA_PATH):
        print(f"ERROR: no se encuentra {SCHEMA_PATH}", file=sys.stderr)
        return 1

    conn = connect(args.db)
    try:
        load_schema(conn)
        if args.seed:
            seed_product(conn)
            print("Producto Jacket Masters inserte (seed).")
        dump(conn)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
