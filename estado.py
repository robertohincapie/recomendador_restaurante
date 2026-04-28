import os
from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel, Field
from enum import Enum
import json

# La definición de los estados estará dado por lo siguiente:
class restaurante(BaseModel):
    nombre: str
    latitud: float
    longitud: float
    categoria: List[str]
    calificacion: float

class pregunta(BaseModel):
    pregunta: str
    opciones: List[str]
    respuestas: Optional[List[str]] = None

class AgentState(BaseModel):
    latitud: float
    longitud: float
    radio: float
    estado: str = Field(default="inicial")  # Estado del agente (inicial, buscando, recomendando, etc.)
    restaurantes: List[restaurante] = []
    preguntas: List[pregunta] = []

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
        return AgentState(latitud=0.0, longitud=0.0, radio=0.0, estado="inicial")  # Estado inicial vacío
    with open(filename, "r", encoding="utf-8") as f:
        data = f.read()
        return AgentState.model_validate_json(data)
    