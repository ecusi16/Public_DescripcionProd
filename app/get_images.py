from googlesearch import search
import requests
from bs4 import BeautifulSoup
import re

def obtener_enlaces_busqueda(query):
    """enlaces = []
    for resultado in search(query, num_results=num_links):
        enlaces.append(resultado)
    return enlaces"""
    # Realizar la búsqueda y obtener el primer resultado
    try:
        first_result = next(search(query, num_results=3))
        return first_result
    except StopIteration:
        return None
    
def es_enlace_video(enlace):
    plataformas_video = ["youtube.com", "vimeo.com", "dailymotion.com"]  # Agrega otras plataformas si es necesario
    for plataforma in plataformas_video:
        if plataforma in enlace:
            return True
    return False

# Función para verificar si un enlace es válido
def es_enlace_valido(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False

def obtener_enlaces_busqueda(row):
    num_links=3
    query = '"{}" "{}"'.format(row.codigo, row.marca)
                 
    second_option = '"{}" ("{}")'.format(row.marca, row.nombre)
    enlaces = []
    for i, resultado in enumerate(search(query, country="BO"), 1):
        if not es_enlace_video(resultado) and es_enlace_valido(resultado):
            enlaces.append(resultado)
        if len(enlaces) == num_links:
            break
    if len(enlaces)==0:
        for i, resultado in enumerate(search(second_option, country="BO"), 1):
            if not es_enlace_video(resultado) and es_enlace_valido(resultado):
                enlaces.append(resultado)
            if len(enlaces) == num_links:
                break
    return enlaces

def buscar_articulo(nombre_articulo):
    query = input(nombre_articulo)
    return obtener_enlaces_busqueda(query)[0]


def obtener_3_imagenes(lista_urls):
    # Extraer los enlaces de las imágenes
    image_links = []
    for url in lista_urls.enlaces:
        try:
            if url is None:
                return []
            # Realizar la solicitud HTTP a la página
            response = requests.get(url)
            response.raise_for_status()  # Verificar si la solicitud fue exitosa

            # Parsear el contenido HTML de la página
            soup = BeautifulSoup(response.content, 'html.parser')

            # Posibles patrones de clases de contenedores de carrusel usando expresiones regulares
            carousel_patterns = [
                re.compile(r'swiper-container.*'),
                re.compile(r'swiper.*'),
                re.compile(r'.*carousel.*'),
                re.compile(r'carousel.*'),
                re.compile(r'slider.*'),
                re.compile(r'image-view--wrap.*'),
                re.compile(r'.*gallery.*'),
                # Agrega otros patrones aquí
            ]

            # Buscar imágenes en posibles carruseles
            for pattern in carousel_patterns:
                carousels = soup.find_all('div', {"class":pattern})
                for carousel in carousels:
                    images = carousel.find_all('img')
                    for img in images:
                        image_url = img.get('src')
                        if es_enlace_valido(image_url) and image_url not in image_links:
                            image_links.append(image_url)

            # Si no se encontraron imágenes en carruseles, buscar una imagen principal
            if not image_links:
                main_image = soup.find('img')
                if main_image:
                    image_url = main_image.get('src')

            if len(image_links)>=3:
                return image_links
        except:
            return image_links
    return image_links

def obtener_imagenes_articulo(nombre_articulo):
    url = buscar_articulo(nombre_articulo)
    return obtener_3_imagenes(url)