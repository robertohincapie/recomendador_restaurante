import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Dict, List
import time


# Simulación de lógica externa
from base import generar_formulario, procesar_respuesta, obtener_resultados, buscar_restaurantes_osm
from estado import AgentState, guardar_estado, cargar_estado, restaurante

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

if(estado.estado=="inicial"):
    #Se debe buscar los restaurantes y generar la primera pregunta
    print("Buscando restaurantes en OSM...")    
    restaurantes = buscar_restaurantes_osm(estado.latitud, estado.longitud, estado.radio)
    print(f"Encontrados {len(restaurantes)} restaurantes.")
    rest=[]
    for r in restaurantes:  # Imprime los primeros 5 restaurantes encontrados
        print(r,'\n')
    #    nombre: str,     latitud: float,    longitud: float,    categoria: List[str],    calificacion: float
        rest.append(restaurante(nombre=r.get("tags", {}).get("name", "Desconocido"),
            latitud=r.get("lat"), longitud=r.get("lon"),
            categoria=r.get("tags", {}).get("cuisine", "Desconocida").split(";"),  # Asumiendo que las categorías están separadas por ";"
            calificacion=0.0  # Placeholder, ya que OSM no proporciona calificaciones
            ))
    estado.restaurantes=rest
    guardar_estado(estado)
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





