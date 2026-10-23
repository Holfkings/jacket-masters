-- ============================================================================
-- jacket-masters — SQLite schema
-- Fuente de datos: detección automática del video (ffprobe/ffmpeg) + reporte
-- de la sala de diseño. 521 frames, 720x720, h264/60fps.
--
-- Contrato REST que consumen el frontend y el FastAPI:
--   GET  /api/product   -> tallas, colores, precios y SKUs
--   POST /api/newsletter-> suscripción del footer
--
-- Notas de diseño
-- ----------------------------------------------------------------------------
-- - `products` + `variants` + `images` es el modelo de "skew" típico de
--   e-commerce: el producto es la plantilla, las variantes son talla+color
--   con SKU e inventario propios.
-- - Los precios se guardan en CENTS (INTEGER) para evitar errores de
--   redondeo con el tipo float. El frontend divide por 100 y añade la
--   moneda.
-- - `newsletter_subscribers` guarda solo el email y el estado; la confirmación
--   del token se genera en el FastAPI y se envía por correo (no está en este
--   schema por no mezclar capas). Los boletines duplicados se evitan con
--   `UNIQUE(email COLLATE NOCASE)`.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- --- productos -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    handle        TEXT NOT NULL UNIQUE,          -- slug amigable (jacket-masters)
    name          TEXT NOT NULL,                 -- Puffer Masters
    tagline       TEXT NOT NULL,                 -- Stand out Without trying
    sku           TEXT NOT NULL,                 -- sku del producto (fila única)
    original_price INTEGER NOT NULL,             -- precio original, en CENTS
    sale_price    INTEGER,                       -- precio de oferta, en CENTS
    description   TEXT NOT NULL DEFAULT '',      -- blurb de la landing
    status        TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','draft','archived')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);

-- --- variantes (talla + color + SKU + inventario) --------------------------
-- Único (product_id, size, color) garantiza que no haya variantes duplicadas.
CREATE TABLE IF NOT EXISTS variants (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    INTEGER NOT NULL
                  REFERENCES products(id) ON DELETE CASCADE,
    size          INTEGER NOT NULL,              -- 36 / 38 / 40
    color         TEXT NOT NULL,                 -- orange / black / red
    color_hex     TEXT NOT NULL,                 -- #e8a849 / #0c0c0c / #c0392b
    sku           TEXT NOT NULL,
    stock         INTEGER NOT NULL DEFAULT 0,    -- unidades disponibles
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (product_id, size, color)
);
CREATE INDEX IF NOT EXISTS idx_variants_product ON variants(product_id);

-- --- galería de imágenes (carrusel del hero + cards) -----------------------
-- La ruta `url` apunta a una imagen real del producto. El video no tiene
-- núcleo gráfico decente, así que este tablón se llena con fotos del
-- cliente o librería libre; el SVG actualmente usado en el HTML es un
-- placeholder del sitio, no se guarda aquí.
CREATE TABLE IF NOT EXISTS images (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL
                REFERENCES products(id) ON DELETE CASCADE,
    sort_order  INTEGER NOT NULL,
    url         TEXT NOT NULL,
    alt         TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_images_product ON images(product_id);

-- --- newsletter ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS newsletter_subscribers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','confirmed','bounced')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    confirmed_at TEXT,
    UNIQUE (email COLLATE NOCASE)
);
CREATE INDEX IF NOT EXISTS idx_newsletter_status ON newsletter_subscribers(status);

-- --- configuración del sitio (valores que pueden cambiarse sin código) -----
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
