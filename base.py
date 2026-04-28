from estado import AgentState, guardar_estado, cargar_estado, pregunta

def generar_formulario():
    estado=cargar_estado()
    if len(estado.preguntas)>0:
        pregunta=estado.preguntas[-1]
        if pregunta.tipo == "open":
            cad=f"""            
<h2>{pregunta.pregunta}</h2>
<form action="/encuesta_post/" method="post">
    <textarea name="respuesta_abierta" rows="4" cols="50" required></textarea><br>
    <button type="submit">Enviar</button>
</form>
"""
            return cad
        input_type = "radio" if pregunta.tipo == "single" else "checkbox"
        opc=""
        for opcion in pregunta.opciones:
            opc+=f'<label><input type="{input_type}" name="opciones" value="{opcion}">{opcion}</label><br>'
        max_note = f"Maximo {pregunta.max_respuestas} respuestas." if pregunta.tipo == "multiple" else ""
        cad=f"""            
<h2>{pregunta.pregunta}</h2>
<p>{max_note}</p>
<form action="/encuesta_post/" method="post">
    {opc}
    <button type="submit">Enviar</button>
</form>
"""
        return cad
    else:
        return "Aún no ha comenzado el proceso de búsqueda de restaurantes. Por favor espere"
        
def procesar_respuesta(opciones=None, respuesta_abierta: str = ""):
        estado=cargar_estado()
        if len(estado.preguntas) == 0:
            return []
        pregunta_actual=estado.preguntas[-1]
        if pregunta_actual.respuestas is None:
            pregunta_actual.respuestas = []
        respuestas_guardadas = []
        if pregunta_actual.tipo == "open":
            valor = (respuesta_abierta or "").strip()
            if valor:
                pregunta_actual.respuestas.append(valor)
                respuestas_guardadas.append(valor)
        elif pregunta_actual.tipo == "single":
            seleccion = []
            if isinstance(opciones, list):
                seleccion = opciones[:1]
            elif isinstance(opciones, str) and opciones.strip():
                seleccion = [opciones.strip()]
            for valor in seleccion:
                pregunta_actual.respuestas.append(valor)
                respuestas_guardadas.append(valor)
        else:
            seleccion = []
            if isinstance(opciones, list):
                seleccion = opciones[:pregunta_actual.max_respuestas]
            elif isinstance(opciones, str) and opciones.strip():
                seleccion = [opciones.strip()]
            for valor in seleccion:
                pregunta_actual.respuestas.append(valor)
                respuestas_guardadas.append(valor)
        estado.preguntas[-1]=pregunta_actual
        guardar_estado(estado)
        return respuestas_guardadas
    

def obtener_resultados():
    return []
