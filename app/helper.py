import requests
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np

##################### FORMAT functions ############################

# Formatear las columnas de listas como viñetas
def format_list_as_bullets(lst):
    try:
        if len(lst)==0: 
            return ""
        items = lst
        return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"
    except Exception as e:
        return ""

# Formatear las columnas de listas como viñetas y enlaces clicables
def format_list_as_bullets_and_links(lst):
    try:
        if len(lst)==0:
            return ""
        items = lst 
        return "<ul>" + "".join(f"<li><a href='{item}' target='_blank'>{item}</a></li>" for item in items) + "</ul>"
    except Exception as e:
        return ""
    
##################### CHECK functions ############################

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

# Función para verificar si un enlace es válido
def es_enlace_valido(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Función para verificar todos los enlaces en una fila
def verificar_fila_enlaces(row, key1, key2):
    try:
        for link in row[key1] + row[key2]:
            if  (not es_enlace_valido(link)):
                return False
        return True
    except Exception as e:
        return False

##################### CONVERT functions ############################

# Opción para descargar el archivo con descripciones
def convert_df_to_xlsx(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

##################### PARALLEL functions ############################


# Función principal para paralelizar la tarea
def parallel_apply_formatting(df, columns, func, num_workers=4):
    df_split = np.array_split(df, num_workers)
    # Lista para guardar las futuras particiones
    futures = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
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
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(verificar_enlaces_partition, part, enlaces_col, imagenes_col) for part in df_split]
        results = [future.result() for future in futures]
    return pd.concat(results)


# Función para aplicar web scraping en paralelo
def aplicar_en_paralelo(df, func, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        resultados = list(executor.map(func, [row for index, row in df.iterrows()]))
    return resultados

# Función para aplicar la formateo a una columna
def apply_formatting(df, column, func):
    df[column] = df[column].apply(func)
    return df