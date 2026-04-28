import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Optional
import time

from base import generar_formulario, procesar_respuesta, obtener_resultados
from estado import AgentState, guardar_estado, cargar_estado, pregunta
from question_tool import QuestionDesigner, QuestionDesignRequest

app = FastAPI()
designer = QuestionDesigner()
PRIMERA_PREGUNTA = "¿Qué tipo de comida prefieres?"

if(os.path.exists("estado.json")):
        estado=cargar_estado()
else: 
    estado=AgentState(latitud=6.2408979, longitud=-75.5904892, radio=1000.0)
    guardar_estado(estado)  

estado_global = {
    "ultima_actualizacion": time.time(),
    "estado": estado   
}

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

@app.post("/encuesta_post/")
async def encuesta_post(
    opciones: Optional[list[str]] = Form(None),
    respuesta_abierta: str = Form(default="")
):
    print("Procesando encuesta...")
    print("Recibida respuesta de encuesta:", opciones, respuesta_abierta)
    respuestas_actuales = procesar_respuesta(opciones=opciones, respuesta_abierta=respuesta_abierta)
    estado = cargar_estado()
    if len(estado.preguntas) == 1 and estado.preguntas[0].pregunta == PRIMERA_PREGUNTA:
        comidas = []
        for valor in respuestas_actuales:
            texto = valor.strip()
            if texto and texto not in comidas:
                comidas.append(texto)
        if comidas:
            if len(comidas) == 1:
                objective = f"Para comida {comidas[0]}, ¿qué factor priorizas al elegir restaurante?"
                candidate_options = ["Precio", "Cercania", "Calificacion", "Rapidez", "Ambiente"]
            else:
                objective = "De las comidas que elegiste, ¿cuál quieres priorizar hoy?"
                candidate_options = comidas
            second_request = QuestionDesignRequest(
                objective=objective,
                context="Pregunta de seguimiento para personalizar recomendacion",
                expected_answers=max(5, len(comidas) * 3),
                candidate_options=candidate_options,
            )
            blueprint = designer.design(second_request)
            nueva_pregunta = pregunta(
                pregunta=blueprint.question,
                tipo=blueprint.question_type.value,
                opciones=blueprint.options,
                min_respuestas=blueprint.min_answers,
                max_respuestas=blueprint.max_answers,
                respuestas=[],
            )
            estado.preguntas.append(nueva_pregunta)
            guardar_estado(estado)

    estado_global["ultima_actualizacion"] = time.time()

    return RedirectResponse(url="/", status_code=303)


@app.get("/check_update/")
async def check_update(last_timestamp: float):
    
    updated = estado_global["ultima_actualizacion"] > last_timestamp

    return JSONResponse({
        "updated": updated,
        "timestamp": estado_global["ultima_actualizacion"]
    })


@app.post("/tool/question")
async def create_question_tool(request: QuestionDesignRequest):
    estado = cargar_estado()
    if len(estado.preguntas) == 0:
        first_request = QuestionDesignRequest(
            objective=PRIMERA_PREGUNTA,
            context=request.context,
            expected_answers=request.expected_answers,
            candidate_options=request.candidate_options,
        )
        blueprint = designer.design(first_request)
    else:
        blueprint = designer.design(request)
    nueva_pregunta = pregunta(
        pregunta=blueprint.question,
        tipo=blueprint.question_type.value,
        opciones=blueprint.options,
        min_respuestas=blueprint.min_answers,
        max_respuestas=blueprint.max_answers,
        respuestas=[],
    )
    estado.preguntas.append(nueva_pregunta)
    guardar_estado(estado)
    estado_global["ultima_actualizacion"] = time.time()
    return JSONResponse(
        {
            "question": blueprint.question,
            "question_type": blueprint.question_type.value,
            "min_answers": blueprint.min_answers,
            "max_answers": blueprint.max_answers,
            "options": blueprint.options,
        }
    )
