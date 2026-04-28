import os
from typing import List, Optional
from pydantic import BaseModel, Field
import json

# La definición de los estados estará dado por lo siguiente:
class restaurante(BaseModel):
    nombre: str
    latitud: float
    longitud: float
    categoria: str
    calificacion: float

class pregunta(BaseModel):
    pregunta: str
    tipo: str = "multiple"
    opciones: List[str] = Field(default_factory=list)
    min_respuestas: int = 1
    max_respuestas: int = 1
    respuestas: Optional[List[str]] = Field(default_factory=list)

class AgentState(BaseModel):
    latitud: float
    longitud: float
    radio: float
    estado: str = Field(default="inicial")
    restaurantes: List[restaurante] = Field(default_factory=list)
    preguntas: List[pregunta] = Field(default_factory=list)

#métodos para enviar a un archivo json y leer del archivo json
def guardar_estado(estado: AgentState, filename: str = "estado.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            estado.model_dump(),
            f,
            indent=2,
            ensure_ascii=False
        )

def cargar_estado(filename: str = "estado.json") -> AgentState:
    if not os.path.exists(filename):
        return AgentState(latitud=0.0, longitud=0.0, radio=0.0, estado="inicial")
    with open(filename, "r", encoding="utf-8") as f:
        data = f.read()
        return AgentState.model_validate_json(data)
    
