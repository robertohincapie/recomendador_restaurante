import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Dict, List
import time


# Simulación de lógica externa
from base import generar_formulario, procesar_respuesta, obtener_resultados
from estado import AgentState, guardar_estado, cargar_estado

app = FastAPI()

# Estado simple en memoria (puedes migrar a Redis o DB)
if(os.path.exists("estado.json")):
        estado=cargar_estado()
else: 
    estado=AgentState(latitud=6.2408979, longitud=-75.5904892, radio=1000.0)  # Estado inicial vacío
    guardar_estado(estado)  

estado_global = {
    "ultima_actualizacion": time.time(),
    "estado": estado   
}

# -----------------------------
# GET: Página principal
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    print("Cargando estado...")
    print(estado_global['estado'])
    formulario = generar_formulario()
    cad=f"""<!DOCTYPE html>
<html>
<meta charset="UTF-8">
<head>
    <title>Recomendador de Restaurantes</title>
</head>
<body>
    <h1>Recomendador de Restaurantes</h1>
    {formulario}
</body>
</html>"""
    
    return HTMLResponse(content=cad, status_code=200, media_type="text/html; charset=utf-8")

# -----------------------------
# POST: Recepción encuesta
# -----------------------------
@app.post("/encuesta_post/")
async def encuesta_post(opciones: list[str] = Form(None)):
    print("Procesando encuesta...")
    data=opciones
    print("Recibida respuesta de encuesta:", data)
    procesar_respuesta(data)

    # marcar actualización
    estado_global["ultima_actualizacion"] = time.time()

    return RedirectResponse(url="/", status_code=303)


# -----------------------------
# Endpoint para auto-refresh (polling)
# -----------------------------
@app.get("/check_update/")
async def check_update(last_timestamp: float):
    
    updated = estado_global["ultima_actualizacion"] > last_timestamp

    return JSONResponse({
        "updated": updated,
        "timestamp": estado_global["ultima_actualizacion"]
    })