from pydantic import BaseModel


class Sticker(BaseModel):
    id: int
    nombre: str
    pais: str
    numero: int
    rareza: str
    coleccionado: bool
