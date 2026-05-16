from pydantic import BaseModel
from typing import Literal


class Sticker(BaseModel):
    id: int
    nombre: str
    pais: str
    numero: int
    rareza: Literal["comun", "raro", "legendario"]
    coleccionado: bool
    numero_album: int
