from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import json
import estado
load_dotenv(dotenv_path=".env", override=True)
import time
from typing import Dict, List
from estado import AgentState, guardar_estado, cargar_estado, pregunta
import requests

def generar_formulario():
    #Este verifica si hay preguntas pendientes y genera el formulario correspondiente
    # Si no hay preguntas pendientes, genera el formulario de ubicación
    # En esta rutina no hay inteligencia. Solo la generación de la página que contiene el formulario
    # para que el usuario responda a la pregunta que se le hizo
    estado=cargar_estado()
    if len(estado.preguntas)>0:
        pregunta=estado.preguntas[-1]
        opc=""
        for opcion in sorted(pregunta.opciones):
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
    estado=cargar_estado()
    pregunta=estado.preguntas[-1]
    if(data is None):
        print('No se recibieron respuestas. Igual se verificará si se debe generar una nueva pregunta por timeout...')
    else:   
        for di in data:
            pregunta.respuestas.append(di)
        pregunta.numero_respuestas+=1
        estado.preguntas[-1]=pregunta
    tiempo_actual=time.time()
    tiempo_transcurrido=tiempo_actual-estado.tiempo_inicio
    print('Tiempo transcurrido desde la formulación de la pregunta:', tiempo_transcurrido, 'segundos')
    if(pregunta.numero_respuestas>10 or tiempo_transcurrido>300): # PARA MODIFICAR, UMBRAL DE RESPUESTAS
        print('Se han recibido suficientes respuestas. Se procede a generar una nueva pregunta...')
        estado.estado="nueva_pregunta"
        guardar_estado(estado)
        #Ahora llamamos al método de construcción de nueva pregunta, que se encargará de analizar las respuestas y generar una nueva pregunta si es necesario
        construir_nueva_pregunta()
    else: 
        print(f'Se han recibido {pregunta.numero_respuestas} respuestas. Se esperan más respuestas antes de generar una nueva pregunta...')
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

def construir_nueva_pregunta():
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    print('\nAgente encargado de construir una nueva pregunta de acuerdo con el estado del sistema')
    estado=cargar_estado()
    
    if(estado.estado=="nueva_pregunta"): #Se llama al método apropiado para construir la pregunta
        print("Construyendo pregunta para el usuario...")
        estado.tiempo_inicio=time.time() #Guardamos el tiempo de inicio de la pregunta para luego tomar decisiones por timeout
        #Verificamos si el campo de preguntas está vacío. Si es así, se genera la primera pregunta. Si no, se genera una nueva pregunta de acuerdo con las respuestas anteriores
        if len(estado.preguntas)==0:
            preg="¿Qué tipo de comida prefieres?"
            tipos=set()
            for r in estado.restaurantes:
                for c in r.categoria:
                    tipos.add(c)
            pregunta_nueva=pregunta(pregunta=preg, opciones=list(tipos), respuestas=[], numero_respuestas=0)
            estado.preguntas.append(pregunta_nueva)
            estado.estado="esperar_respuesta"
            guardar_estado(estado)
        else: #Ya se cuenta con preguntas y seguro con respuestas. Se debe generar una nueva pregunta de acuerdo con las respuestas anteriores
            print("Generando nueva pregunta de acuerdo con las respuestas anteriores...")
            restaurantes_json=[{"nombre": r.nombre, "categorias": r.categoria} for r in estado.restaurantes]
            restaurantes_str=restaurantes_json.__str__()
            sistema = SystemMessage(
                content=f"""
Eres un motor de decisión iterativo especializado en agregación de preferencias colectivas para selección de restaurantes. Tu función es analizar respuestas de usuarios a preguntas cerradas y generar la siguiente pregunta que reduzca progresivamente el espacio de decisión hasta llegar a una selección final óptima.
Entrada esperada:
Recibirás un objeto JSON con los siguientes campos:
pregunta: texto de la pregunta anterior.
opciones: lista de opciones disponibles en la pregunta anterior.
respuestas: lista de respuestas seleccionadas por los usuarios.
restaurantes: lista de objetos con estructura: nombre, latitud, longitud, categoria: lista de categorías asociadas, calificacion: valor numérico (puede estar en 0.0 si no hay datos)

Objetivo: Tu objetivo es reducir iterativamente el espacio de opciones para converger hacia una decisión final (uno o dos restaurantes altamente preferidos por el grupo).

Lógica de decisión: 
Debes aplicar las siguientes reglas:
1. Análisis de frecuencia
Calcula la frecuencia de cada opción en respuestas.
Identifica:
Opciones dominantes (alta frecuencia relativa)
Opciones marginales (baja o nula frecuencia)
2. Filtrado inicial
Elimina opciones con baja representatividad (por ejemplo, frecuencia ≤ 1 si hay suficiente muestra).
Prioriza las opciones con mayor consenso.
3. Cruce con restaurantes
Filtra los restaurantes cuya categoria coincida con las opciones dominantes.
Si una categoría no tiene restaurantes asociados, debe ser descartada en la siguiente iteración.
4. Reducción del espacio

Dependiendo del estado:
Caso A: Alta dispersión
Si hay muchas opciones con frecuencias similares → agrupar o seleccionar top N (máximo 5).
Caso B: Concentración clara
Si 1–3 opciones dominan, entonces reducir solo a esas.
Caso C: Etapa avanzada
Si ya hay pocas opciones (≤ 3):
Cambiar el enfoque de la pregunta hacia restaurantes específicos en lugar de categorías.
5. Transición a selección final
Cuando haya ≤ 5 restaurantes candidatos:
Genera una pregunta directa sobre restaurantes específicos.
Cuando haya ≤ 2 restaurantes:
La siguiente iteración debe permitir decisión final.
En caso de que sea la iteración final y no se requiera hacer más preguntas, entonces 
la pregunta debe ser: "Las opciones finales son: " y las opciones deben ser los nombres de los restaurantes restantes.

Construcción de la nueva pregunta
Debes generar una nueva pregunta que:
Sea coherente con el contexto anterior, Reduzca el número de opciones, Sea clara, concreta y orientada a decisión
En la formulación de la pregunta, debes especificar si el usuario está eligiendo entre categorías, subcategorías o restaurantes específicos, dependiendo del estado del proceso iterativo.
Tipos de preguntas posibles:
Filtrado por categoría (reducción)
Subcategoría o estilo (ej: tipo de comida dentro de una categoría)
Selección directa de restaurantes
Formato de salida (OBLIGATORIO)

Debes responder únicamente con un JSON válido con esta estructura:

{{
  "pregunta": "texto de la nueva pregunta",
  "opciones": ["opcion1", "opcion2", "..."],
  "respuestas": []
}}

Restricciones:
No incluyas explicaciones, razonamientos ni texto adicional fuera del JSON.
No repitas opciones irrelevantes o sin respaldo en los datos.
No inventes categorías o restaurantes que no estén en la entrada.
Evita mantener más de 5 opciones salvo que sea estrictamente necesario por dispersión.

Criterio de optimización
Estás optimizando una función implícita de consenso grupal:
Maximizar acuerdo colectivo
Minimizar número de iteraciones
Garantizar viabilidad (existencia real de restaurantes)
"""
                )
    
            usuario = HumanMessage(
                content=f""" 
Se presenta el estado actual de un proceso iterativo de decisión grupal orientado a la selección de un restaurante. La información incluye la última pregunta formulada, las opciones disponibles en dicha pregunta, y las respuestas emitidas por los usuarios.
Adicionalmente, se proporciona un conjunto de restaurantes candidatos, cada uno con sus categorías asociadas. Estas categorías son consistentes con las opciones planteadas en las preguntas.
Tu tarea es analizar este estado actual y generar la siguiente pregunta, de tal manera que se reduzca progresivamente el espacio de decisión, acercando al grupo hacia una selección final. Debes priorizar las opciones con mayor consenso y descartar aquellas con baja representatividad o sin correspondencia con restaurantes reales.
La salida debe construirse exclusivamente en el formato JSON especificado, representando una nueva pregunta con sus opciones, sin incluir respuestas.
A continuación, se presenta la información actual del proceso:
- Pregunta anterior: {estado.preguntas[-1].pregunta}
- Opciones anteriores: {estado.preguntas[-1].opciones}
- Respuestas recibidas: {estado.preguntas[-1].respuestas}
- Restaurantes candidatos: {restaurantes_str}
"""
            )
            print('Se debe correr el análisis en el LLM')
            respuesta = llm.invoke([sistema, usuario]).content
            print('Respuesta del LLM:', respuesta)
            data = json.loads(respuesta)
            print(type(data))
            print(data['pregunta'])
            #Ahora se debe guardar la nueva pregunta en el estado
            nueva_pregunta=pregunta(pregunta=data['pregunta'], opciones=data['opciones'], respuestas=[], numero_respuestas=0)
            estado.preguntas.append(nueva_pregunta)
            estado.estado="esperar_respuesta"
            guardar_estado(estado)
