#!/usr/bin/env python3
"""Catalog seed script for Artisan.

Populates the database (SQLite or PostgreSQL) with authentic artisan products
categorized into Bisutería and Marroquinería, linked to optimized WebP images.
Idempotent and safe to run multiple times.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List

from db_utils import connect_db, ensure_schema

PRODUCTS_DATA: List[Dict[str, Any]] = [
    {
        'nombre': 'Aretes de Mostacilla Checa Flor Silvestre',
        'categoria': 'Bisutería',
        'precio': 35000.0,
        'descripcion': (
            'Aretes tejidos a mano con mostacilla checa de alta calibración. '
            'Diseño floral ligero con ganchos antialérgicos en acero quirúrgico. '
            'Cada pieza toma entre 4 y 6 horas de elaboración artesanal dedicada.'
        ),
        'imagen_url': '/static/img/productos/aretes_en_mostacilla_1_IMG_20260120_142208.webp',
        'img2': '/static/img/productos/sdfgh_1_IMG_20260120_142208.webp',
        'img3': '/static/img/productos/sdfghsdfghjdfgh_1_IMG_20260120_142208.webp',
    },
    {
        'nombre': 'Pulsera de Mostacilla Multicolor Étnica',
        'categoria': 'Bisutería',
        'precio': 28000.0,
        'descripcion': (
            'Pulsera ajustable tejida en telar tradicional con patrón geométrico indígena. '
            'Mostacillas resistentes al agua y al desgaste con nudo corredizo de hilo macramé.'
        ),
        'imagen_url': '/static/img/productos/Pulsera_Mostacilla_1_pul_mosta_0_1.webp',
        'img2': '/static/img/productos/Pulsera_Mostacilla_1_pul_mosta_0_2.webp',
        'img3': '/static/img/productos/Pulsera_Mostacilla_1_pul_mosta_0_3.webp',
    },
    {
        'nombre': 'Manilla Delica Miyuki 2 Líneas Minimalista',
        'categoria': 'Bisutería',
        'precio': 42000.0,
        'descripcion': (
            'Manilla fina elaborada con cuentas Delica Miyuki importadas de Japón. '
            'Acabado mate y brillante con telar de alta tensión. '
            'Cierre ajustable adaptable a cualquier tamaño de muñeca.'
        ),
        'imagen_url': '/static/img/productos/Manilla_Delica_2_lineas_1_pul_mosta_0_1.webp',
        'img2': '/static/img/productos/Pulsera_Mostacilla_1_pul_mosta_0_4.webp',
        'img3': '/static/img/productos/Pulsera_Mostacilla_1_pul_mosta_0_5.webp',
    },
    {
        'nombre': 'Manilla Delica Miyuki 3 Líneas Étnica',
        'categoria': 'Bisutería',
        'precio': 55000.0,
        'descripcion': (
            'Diseño de triple hilera con patrón ancestral andino. '
            'Cuentas cilíndricas uniformes con baño de protección UV. '
            'Elegancia sutil y confección 100% artesanal.'
        ),
        'imagen_url': '/static/img/productos/Manilla_Delica_3_lineas_1_pul_mosta_0_1.webp',
        'img2': '/static/img/productos/Pulsera_Mostacilla_1_pul_mosta_0_6.webp',
        'img3': '/static/img/productos/Pulsera_Mostacilla_1_pul_mosta_0_7.webp',
    },
    {
        'nombre': 'Gargantilla Collar Artesanal con Cuentas',
        'categoria': 'Bisutería',
        'precio': 68000.0,
        'descripcion': (
            'Gargantilla tejida a mano con combinación de mostacilla, cristales y piedras naturales. '
            'Broche seguro bañado en oro golfi. Perfecta para ocasiones especiales o uso diario formal.'
        ),
        'imagen_url': '/static/img/productos/joyas_aajjaja_1_IMG_20260120_142717.webp',
        'img2': '/static/img/productos/joyas_aajjaja_1_IMG_20260120_144040_1.webp',
        'img3': '/static/img/productos/joyas_aajjaja_1_IMG_20260121_151620.webp',
    },
    {
        'nombre': 'Billetera Clásica en Cuero Genuino',
        'categoria': 'Marroquinería',
        'precio': 85000.0,
        'descripcion': (
            'Billetera de cuero vacuno curtido al vegetal. '
            'Costuras reforzadas en hilo encerado con 6 ranuras para tarjetas, '
            'compartimento para billetes y bolsillo con broche para monedas.'
        ),
        'imagen_url': '/static/img/productos/casdfg_1_IMG_20260120_143731.webp',
        'img2': '/static/img/productos/sdfgh_3_IMG_20260120_142717.webp',
        'img3': None,
    },
    {
        'nombre': 'Bolso Bandolera en Cuero Vacuno Rústico',
        'categoria': 'Marroquinería',
        'precio': 145000.0,
        'descripcion': (
            'Bolso tipo bandolera elaborado en cuero rústico de alta densidad. '
            'Herrajes en latón envejecido y correa graduable. '
            'Forro interior de lona resistente con doble compartimento interno.'
        ),
        'imagen_url': '/static/img/productos/323r4_1_IMG_20260120_144243_1.webp',
        'img2': '/static/img/productos/sdf_1_IMG_20260120_144452.webp',
        'img3': None,
    },
    {
        'nombre': 'Portadocumentos y Tarjetero en Cuero Curtido',
        'categoria': 'Marroquinería',
        'precio': 48000.0,
        'descripcion': (
            'Tarjetero ultraligero hecho a mano con cortes limpios y bordes pulidos con cera de abeja. '
            'Capacidad para hasta 8 tarjetas y billetes doblados.'
        ),
        'imagen_url': '/static/img/productos/zxcvb23456_1_IMG_20260120_141919.webp',
        'img2': '/static/img/productos/sdfgh_2_IMG_20260120_142315.webp',
        'img3': None,
    },
]


def seed_database() -> None:
    """Seeds categories and authentic artisan products."""
    db = connect_db()
    ensure_schema(db)

    # 1. Clean up mock placeholder if present
    try:
        db.execute("DELETE FROM productos WHERE nombre = 'Producto de ejemplo'")
        db.commit()
    except Exception:
        pass

    # 2. Ensure categories exist
    categories = ['Bisutería', 'Marroquinería']
    for cat in categories:
        try:
            # Query first for cross-DB compatibility (Postgres + SQLite)
            existing = db.execute('SELECT id FROM categorias WHERE nombre = ?', (cat,)).fetchone()
            if not existing:
                db.execute('INSERT INTO categorias (nombre) VALUES (?)', (cat,))
        except Exception as exc:
            print(f"[WARN] Category insert failed for {cat}: {exc}", file=sys.stderr)
    db.commit()

    # 3. Insert or update products
    inserted = 0
    updated = 0
    for prod in PRODUCTS_DATA:
        existing = db.execute(
            'SELECT id FROM productos WHERE nombre = ? AND parent_id IS NULL',
            (prod['nombre'],),
        ).fetchone()

        if existing:
            prod_id = existing['id'] if isinstance(existing, dict) else existing[0]
            db.execute(
                '''UPDATE productos
                   SET categoria = ?, precio = ?, descripcion = ?, imagen_url = ?, img2 = ?, img3 = ?
                   WHERE id = ?''',
                (
                    prod['categoria'],
                    prod['precio'],
                    prod['descripcion'],
                    prod['imagen_url'],
                    prod['img2'],
                    prod['img3'],
                    prod_id,
                ),
            )
            updated += 1
        else:
            db.execute(
                '''INSERT INTO productos (nombre, categoria, precio, descripcion, imagen_url, img2, img3, parent_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, NULL)''',
                (
                    prod['nombre'],
                    prod['categoria'],
                    prod['precio'],
                    prod['descripcion'],
                    prod['imagen_url'],
                    prod['img2'],
                    prod['img3'],
                ),
            )
            inserted += 1

    db.commit()

    # 4. Print summary
    rows = db.execute(
        'SELECT id, nombre, categoria, precio, imagen_url FROM productos WHERE parent_id IS NULL ORDER BY id ASC'
    ).fetchall()

    print(f"\nSEED COMPLETE: {inserted} inserted, {updated} updated. Total products: {len(rows)}")
    print("-" * 85)
    for r in rows:
        r_dict = dict(r)
        print(f"[{r_dict['id']:2d}] {r_dict['nombre']:48} | {r_dict['categoria']:14} | ${r_dict['precio']:8,.0f} COP")
    print("-" * 85)
    db.close()


if __name__ == '__main__':
    seed_database()
