from typing import Dict
from estado import AgentState, guardar_estado, cargar_estado, pregunta

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

