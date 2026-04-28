from typing import Dict, List
from estado import AgentState, guardar_estado, cargar_estado, pregunta
import requests

def generar_formulario():
    #Este verifica si hay preguntas pendientes y genera el formulario correspondiente
    # Si no hay preguntas pendientes, genera el formulario de ubicación
    estado=cargar_estado()
    if len(estado.preguntas)>0:
        pregunta=estado.preguntas[-1]
        opc=""
        for opcion in pregunta.opciones:
            opc+=f'<label><input type="checkbox" name="opciones" value="{opcion}">{opcion}</label><br>'
        cad=f"""            
<h2>{pregunta.pregunta}</h2>
<form action="/encuesta_post/" method="post">
    {opc}
    <button type="submit">Enviar</button>
</form>
"""
        return cad
    else:
        return "Aún no ha comenzado el proceso de búsqueda de restaurantes. Por favor espere"
        
def procesar_respuesta(data):
    #print("Procesando respuesta:", data)
        estado=cargar_estado()
        pregunta=estado.preguntas[-1]
        for di in data:
            pregunta.respuestas.append(di)
        estado.preguntas[-1]=pregunta
        guardar_estado(estado)
    

def obtener_resultados():
    # Lógica para obtener resultados
    return []

def buscar_restaurantes_osm(lat: float, lon: float, radio: int = 1000) -> List[Dict]:
    """
    Busca restaurantes en OpenStreetMap alrededor de una coordenada.

    Args:
        lat (float): Latitud del punto central
        lon (float): Longitud del punto central
        radio (int): Radio en metros (default 1000)

    Returns:
        List[Dict]: Lista de restaurantes con latitud, longitud y tags
    """

    #url = "https://overpass.kumi.systems/api/interpreter"
    url='https://overpass-api.de/api/interpreter'
    query = """
    [out:json];
    node["amenity"="restaurant"](around:1000,6.2408979,-75.5904892);
    out;
    """

    headers = {
        "User-Agent": "mi-app-restaurantes/1.0 (roberto.hincapie@gmail.com)",
        "Accept": "application/json"
    }

    response = requests.get(url, params={"data": query}, headers=headers)
    response.raise_for_status()

    data = response.json()

    resultados = []

    for el in data.get("elements", []):
        tags = el.get("tags", {})

        # manejar node vs way/relation
        latitud = el.get("lat") or el.get("center", {}).get("lat")
        longitud = el.get("lon") or el.get("center", {}).get("lon")

        if latitud and longitud:
            resultados.append({
                "lat": latitud,
                "lon": longitud,
                "tags": tags
            })

    return resultados