from openai import OpenAI
import streamlit as st
import re 
import json
import time


# Configurar API de OpenAI
YOUR_API_KEY =  st.secrets["secrets"]["perplexity_api_key"]

def get_description(product_json):
    # Prompt base
    prompt_base = """Toma el rol de un experto en búsqueda de productos y generador de informacion valiosa como: descripcion, caracteristicas principales y listado de ventajas de estos productos, basado en sus codigos de barras, marca y nombre y enlaces de internet

        Te proporcionaré una lista en formato JSON de productos que incluye su código de fabricante, marca, nombre y 3 enlaces de internet de estos productos, es posible que algunas veces no sea posible proporcionar la marca del producto, por lo cual tu debes en base al nombre y el codigo del producto deducir la marca, ademas tendras que realizar las siguientes tareas:

        - proporcionar, para cada producto de la lista, un párrafo introductorio conciso de 5-7 frases que describa el producto y sus características principales
        - proporcionar de 7-10 especificaciones de cada producto en viñetas.
        - proporcionar de 5 - 7 de las ventajas clave de cada producto en viñetas.
        - Incluir los enlaces directos de las fuentes de donde extragiste la informacion de los productos, asegurándote de que estén activos y no devuelvan errores 404, no debes incluir enlaces vacíos o que no devuelvan contenido relevante. 
        - No menciones como ventajas o especificaciones precio o cualquier tipo de garantia.

        Por favor, devuelve estos datos en formato lista de JSON que tenga las siguientes llaves por cada producto, es decir un json por cada producto dentro de una lista: 
        [{\"Codigo\": valor, \"Marca\": valor, \"Nombre\": valor, \"Descripcion\": valor, \"Especificaciones\": valor, \"Ventajas\":valor, \"Enlaces\":valor}, {...} ].
        
        Recuerda que sólo devuelves y respondes con JSON válido e iterable compatible con RFC8259 en tus respuestas
        ¡Gracias!
    """
    print(product_json)
    print("-----------------------------------------------------------------")
    prompt_user = ("lista de productos: {}").format(product_json)

    # Crear el cliente de OpenAI
    client = OpenAI(api_key=YOUR_API_KEY, base_url="https://api.perplexity.ai")

    # Mensajes para la conversación
    messages = [
        {
            "role": "system",
            "content": prompt_base,
        },
        {
            "role": "user",
            "content": prompt_user,
        },
    ]

    retries = 5
    delay = 5  # Puedes ajustar el tiempo de espera entre reintentos

    for attempt in range(retries):
        flag_answer = False
        try:
            # chat completion without streaming
            response = client.chat.completions.create(
                model="llama-3-sonar-large-32k-online",
                messages=messages,
            )
            respuesta = response.choices[0].message.content.strip()
            json_match = re.search(r'\[\s*\{.*\}\s*\]', respuesta, re.DOTALL)
            flag_answer = True
            json_content = json_match.group(0)
            # Convertir el texto JSON en un objeto JSON de Python
            json_data = json.loads(json_content)
            #print("Generado")
            return json_data
        except Exception as e:
            if flag_answer:
                print(f"Error al decodificar JSON: {e}")
                print(respuesta)
                print(f"Retrying...")
                print("================================================================")
            else:
                print("Error 429")
                print(e)
                print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                print("================================================================")
                time.sleep(delay)
    
    #raise Exception("Failed to fetch data after several retries")
    return json.loads('[]')
