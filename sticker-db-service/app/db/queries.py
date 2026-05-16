import time
import logging
from typing import Optional

import asyncpg

from app.db.connection import get_pool

logger = logging.getLogger(__name__)


async def get_all_stickers(
    pais: Optional[str] = None,
    rareza: Optional[str] = None,
) -> tuple[list[dict], float]:
    pool = get_pool()
    sql = "SELECT * FROM stickers WHERE TRUE"
    args: list = []

    if pais:
        args.append(pais)
        sql += f" AND pais = ${len(args)}"
    if rareza:
        args.append(rareza)
        sql += f" AND rareza = ${len(args)}"

    start = time.monotonic()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *args)
    duration_ms = (time.monotonic() - start) * 1000

    logger.info("get_all_stickers returned %d rows in %.2f ms", len(rows), duration_ms)
    return [dict(r) for r in rows], duration_ms


async def get_sticker_by_id(sticker_id: int) -> tuple[Optional[dict], float]:
    pool = get_pool()

    start = time.monotonic()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM stickers WHERE id = $1", sticker_id
        )
    duration_ms = (time.monotonic() - start) * 1000

    logger.info("get_sticker_by_id(%d) in %.2f ms", sticker_id, duration_ms)
    return dict(row) if row else None, duration_ms


async def get_stickers_by_album(numero_album: int) -> tuple[list[dict], float]:
    pool = get_pool()

    start = time.monotonic()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM stickers WHERE numero_album = $1", numero_album
        )
    duration_ms = (time.monotonic() - start) * 1000

    logger.info(
        "get_stickers_by_album(%d) returned %d rows in %.2f ms",
        numero_album,
        len(rows),
        duration_ms,
    )
    return [dict(r) for r in rows], duration_ms
