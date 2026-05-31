"""Каталог мерча (фиксированный набор для учебного проекта)."""

from __future__ import annotations

MERCH_PRODUCTS: list[dict] = [
    {
        "id": "shirt",
        "name": "футболка базовая ВИШ",
        "price": 40,
        "image": "shirt.webp",
    },
    {
        "id": "socks",
        "name": "носки брендированные ВИШ",
        "price": 20,
        "image": "socks.webp",
    },
    {
        "id": "bottle",
        "name": "бутылка для воды ВИШ",
        "price": 50,
        "image": "bottle.webp",
    },
    {
        "id": "stickerpack",
        "name": "стикерпак ВИШ",
        "price": 25,
        "image": "stickerpack.webp",
    },
]

MERCH_BY_ID = {p["id"]: p for p in MERCH_PRODUCTS}
