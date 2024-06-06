import streamlit as st
import os
import pandas as pd
from PIL import Image
import io
import requests
from app.generador import get_description
from app.get_images import obtener_imagenes_articulo, obtener_enlaces_busqueda, obtener_3_imagenes
import json
from io import BytesIO
import concurrent.futures
from datetime import datetime
import numpy as np


# Función principal para paralelizar la tarea
def parallel_apply_formatting(df, columns, func, num_workers=4):
    df_split = np.array_split(df, num_workers)
    # Lista para guardar las futuras particiones
    futures = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        for part in df_split:
            for column in columns:
                futures.append(executor.submit(apply_formatting, part, column,func))
                
        # Esperar y recolectar los resultados, preservando los índices originales
        results = [future.result() for future in futures]
    
    # Concatenar las particiones preservando los índices
    final_df = pd.concat(results).sort_index()
    
    return final_df

# Función para aplicar verificar_fila_enlaces a una partición del DataFrame
def verificar_enlaces_partition(partition, enlaces_col, imagenes_col):
    partition['enlaces_validos'] = partition.apply(lambda x: verificar_fila_enlaces(x, enlaces_col, imagenes_col), axis=1)
    return partition

# Función principal para paralelizar la verificación
def parallel_verificar_enlaces(df, enlaces_col, imagenes_col, num_workers=4):
    df_split = np.array_split(df, num_workers)
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(verificar_enlaces_partition, part, enlaces_col, imagenes_col) for part in df_split]
        results = [future.result() for future in futures]
    return pd.concat(results)
# Opción para descargar el archivo con descripciones
def convert_df_to_xlsx(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# Formatear las columnas de listas como viñetas
def format_list_as_bullets(lst):
    try:
        if len(lst)==0: #pd.isna(lst):
            return ""
        items = lst #.split(", ")
        return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"
    except Exception as e:
        return ""

# Formatear las columnas de listas como viñetas y enlaces clicables
def format_list_as_bullets_and_links(lst):
    try:
        if len(lst)==0: #pd.isna(lst):
            return ""
        items = lst #.split(", ")
        return "<ul>" + "".join(f"<li><a href='{item}' target='_blank'>{item}</a></li>" for item in items) + "</ul>"
    except Exception as e:
        return ""

# Función para manejar imágenes embebidas
def fetch_image(url):
    response = requests.get(url)
    img = Image.open(io.BytesIO(response.content))
    return img

# Función para aplicar web scraping en paralelo
def aplicar_en_paralelo(df, func, max_workers=5):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        resultados = list(executor.map(func, [row for index, row in df.iterrows()]))
    return resultados

# Función para verificar si un enlace es válido
def es_enlace_valido(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Función para verificar todos los enlaces en una fila
def verificar_fila_enlaces(row, key1, key2):
    for link in row[key1] + row[key2]:
        if  (not es_enlace_valido(link)):
            return False
    return True

# Función para aplicar la formateo a una columna
def apply_formatting(df, column, func):
    print(column)
    df[column] = df[column].apply(func)
    return df

# Función para verificar columnas requeridas
def check_required_columns(df, required_columns):
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, missing_columns
    return True, []

# Función para verificar filas vacías
def check_empty_rows(df):
    empty_rows = df[df.isnull().all(axis=1)]
    return empty_rows

# Función principal de la aplicación
def main():
    try:
        # Definir columnas requeridas
        required_columns = ['codigo', 'marca', 'nombre']
        df_enlaces_invalidos = None
        df_enlaces_validos = None
        st.markdown(
            """
            <style>
            .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
            .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
            .viewerBadge_text__1JaDK {
                display: none;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        st.title("Generador de descripciones productos")
        st.write("Por favor, asegúrate de que el archivo Excel que subas empiece en la fila 1 (como la imagen inferior), tenga los encabezados en minúscula y sin acentos, y que contenga obligatoriamente las siguientes tres columnas: ")
        lista = ["**codigo** para el código de barras", "**marca** para la marca del producto", "**nombre** para el nombre del producto"]
        for item in lista:
            st.markdown(f"- {item}")
        # Ruta al archivo de imagen
        image_path = "app/data/imagen_excel.png"

        # Leer la imagen usando PIL
        image = Image.open(image_path)

        # Centrar la imagen usando HTML en st.markdown
        st.markdown(
            """
            <style>
            .center-image {
                display: flex;
                justify-content: center;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="center-image">', unsafe_allow_html=True)
        st.image(image, caption='Formato del archivo excel a subir')
        st.markdown('</div>', unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Sube tu archivo de Excel", type=["xlsx", "xls"])
        
        if uploaded_file:
            df = pd.read_excel(uploaded_file, header=0)
            # Verificar columnas requeridas
            is_valid, missing_columns = check_required_columns(df, required_columns)
            
            if not is_valid:
                df = pd.DataFrame({'codigo': [], 'marca': [], 'nombre': []})
                st.error(f"El archivo cargado no contiene las columnas requeridas: {', '.join(missing_columns)}")

            # Verificar filas vacías
            empty_rows = check_empty_rows(df)
            if not empty_rows.empty:
                df = pd.DataFrame({'codigo': [], 'marca': [], 'nombre': []})
                st.error("El archivo contiene filas completamente vacías, por favor virifique que el archivo no contenga filas vacias y que solo tenga una cabecera general ('codigo', 'marca', 'nombre')")
            st.write("Vista previa de los datos:")
            st.dataframe(df[['codigo', 'marca', 'nombre']])
            
            # Campo de entrada para el nombre del archivo
            export_file = os.path.splitext(uploaded_file.name)[0]
            file_name = st.text_input("Nombre base del archivo", value=export_file)

            if st.button("Generar descripciones"):
                with st.spinner('Ejecutando la función, por favor espere y no recargue la pagina...'):
                    results = []
                    json_result = None
                    lista_productos = []

                    t1 = datetime.now()
                    df["enlaces"] = aplicar_en_paralelo(df, obtener_enlaces_busqueda)
                    t2 = datetime.now()
                    print("Busqueda google")
                    print(t2-t1)

                    t1 = datetime.now()
                    df['Imagenes'] = aplicar_en_paralelo(df, obtener_3_imagenes)
                    t2 = datetime.now()
                    print("Scrapping")
                    print(t2-t1)

                    for i in range(0, len(df), 2):
                        # Seleccionar dos filas
                        subset_df = df.iloc[i:i+2]
                        lista_productos.append(subset_df)

                    t1 = datetime.now()
                    # Procesar filas en paralelo
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        # add links sencond version
                        results = list(executor.map(get_description, \
                                                    [subset_df[['codigo','marca', \
                                                    'nombre', 'enlaces']].to_json(orient="records") \
                                                    for subset_df in lista_productos]))
                    t2 = datetime.now()
                    print("Perplexity time")
                    print(t2-t1)

                    # Combinar los JSONs
                    for json_obj in results:
                        if json_result is None:
                            json_result = json_obj
                        else:
                            json_result = json_result + json_obj
                    
                    results_df = pd.DataFrame(json_result)

                    t1 = datetime.now()
                    #['Codigo', 'Marca', 'Nombre', 'Especificaciones', 'Ventajas', 'Enlaces']
                    results_df['Especificaciones1'] = results_df['Especificaciones']
                    results_df['Ventajas1'] = results_df['Ventajas']

                    results_df['Especificaciones'] = results_df['Especificaciones'].apply(format_list_as_bullets)
                    results_df['Ventajas'] = results_df['Ventajas'].apply(format_list_as_bullets)

                    results_df['Enlaces1'] = results_df['Enlaces']
                    results_df['Enlaces'] = results_df['Enlaces'].apply(format_list_as_bullets_and_links)

                    df = df.rename(columns={'codigo': 'Codigo', 'marca': 'Marca', 'nombre': 'Nombre'})
                    results_df = df[['Codigo', 'Marca', 'Nombre','Imagenes']].merge(\
                        results_df[['Descripcion', 'Codigo', 'Especificaciones1', 'Especificaciones', 'Ventajas1', 'Ventajas', 'Enlaces1', 'Enlaces']], on='Codigo', how='left')
                    results_df['Imagenes1'] = results_df['Imagenes']
                    results_df['Imagenes'] = results_df['Imagenes'].apply(format_list_as_bullets_and_links)
                    
                    t2 = datetime.now()
                    print("Format time")
                    print(t2-t1)
                    
                    t1 = datetime.now()
                    # Aplicar la verificación de enlaces en paralelo
                    if len(results_df) > 20:
                        results_df = parallel_verificar_enlaces(results_df, 'Enlaces1', 'Imagenes1')
                    else: 
                        results_df['enlaces_validos'] = results_df.apply(lambda x: verificar_fila_enlaces(x, 'Enlaces1', 'Imagenes1'), axis=1)
                    
                    t2 = datetime.now()
                    print("verificar enlaces")
                    print(t2-t1)

                    # Eliminar filas duplicadas basado en la columna 'codigo'
                    results_df = results_df.drop_duplicates(subset='Codigo', keep='first')

                    results_df.loc[results_df['Descripcion'].isna(), 'enlaces_validos'] = False

                    df_enlaces_validos = results_df[results_df['enlaces_validos'] == True].drop(columns=['enlaces_validos'])
                    df_enlaces_invalidos = results_df[results_df['enlaces_validos'] == False].drop(columns=['enlaces_validos'])

                    # Añadir CSS para ajustar el estilo de la tabla
                    st.markdown(
                        """
                        <style>
                        .dataframe tbody tr td {
                            max-width: 150px;
                            word-wrap: break-word;
                            white-space: pre-wrap;
                        }
                        .dataframe tbody tr td ul {
                            padding-left: 20px;  /* Ajustar el margen izquierdo de las viñetas */
                        }
                        </style>
                        """, unsafe_allow_html=True
                    )

                    st.session_state['df_enlaces_validos'] = df_enlaces_validos
                    st.session_state['df_enlaces_invalidos'] = df_enlaces_invalidos

            if 'df_enlaces_validos' in st.session_state:
                # Mostrar el contenido del archivo CSV
                df_enlaces_validos = st.session_state['df_enlaces_validos']
                df_enlaces_invalidos = st.session_state['df_enlaces_invalidos']

                if  len(df_enlaces_invalidos)>0:
                    st.write("Descarga las tablas en excel:")
                else:
                    st.write("Descarga la tabla de resultados:")

                if st.download_button(
                        label=f"Descargar descripciones validas: {len(df_enlaces_validos)} productos",
                        data=convert_df_to_xlsx(df_enlaces_validos[['Codigo', 'Marca', 'Nombre', 'Descripcion', 'Especificaciones1', 'Ventajas1', 'Enlaces1','Imagenes1'
                                        ]]),
                        file_name=f'{file_name}_descripciones.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    ):
                        st.success("Archivo descripciones descargado")

                if len(df_enlaces_invalidos)>0:
                    if st.download_button(
                        label=f"Descargar descripciones para revision: {len(df_enlaces_invalidos)} productos",
                        data=convert_df_to_xlsx(df_enlaces_invalidos[['Codigo', 'Marca', 'Nombre', 'Descripcion', 'Especificaciones1', 'Ventajas1', 'Enlaces1','Imagenes1'
                                        ]]),
                        file_name=f'{file_name}_descripciones_a_revisar.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    ):
                        st.success("Archivo descripciones para segunda revision descargado")


                st.write("Resultados obtenidos:")
                st.write(df_enlaces_validos[['Codigo', 'Marca', 'Nombre', 'Descripcion', 'Especificaciones', 'Ventajas', 'Enlaces','Imagenes'
                                    ]].to_html(escape=False), unsafe_allow_html=True)

                # Mostrar el contenido del archivo CSV
                if len(df_enlaces_invalidos)>0:
                    st.write("Resultados que necesitan revision extra:")
                    st.write(df_enlaces_invalidos[['Codigo', 'Marca', 'Nombre', 'Descripcion', 'Especificaciones', 'Ventajas', 'Enlaces','Imagenes'
                                        ]].to_html(escape=False), unsafe_allow_html=True)
    except Exception as e:
        st.error("Ha ocurrido un error inesperado. Por favor, recarga la página.")
        #st.rerun()
    
            
        
if __name__ == "__main__":
    main()
