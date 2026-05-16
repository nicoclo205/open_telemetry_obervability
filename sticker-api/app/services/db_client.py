import os

import httpx
from opentelemetry import propagate

DB_SERVICE_URL = os.getenv("DB_SERVICE_URL", "http://localhost:8001")


class DbClient:
    def __init__(self) -> None:
        self.base_url = DB_SERVICE_URL

    async def get_all(self, pais: str = None, rareza: str = None) -> list[dict]:
        headers = {}
        propagate.inject(headers)
        params = {k: v for k, v in {"pais": pais, "rareza": rareza}.items() if v is not None}
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get("/stickers", params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    async def get_by_id(self, id: int) -> dict:
        headers = {}
        propagate.inject(headers)
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(f"/stickers/{id}", headers=headers)
            response.raise_for_status()
            return response.json()

    async def get_by_album(self, numero_album: int) -> list[dict]:
        headers = {}
        propagate.inject(headers)
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(f"/stickers/album/{numero_album}", headers=headers)
            response.raise_for_status()
            return response.json()
