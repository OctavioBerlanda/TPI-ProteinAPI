import requests
import json
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuración de la API ---
BASE_ANNOTATIONS_URL = "https://alphafold.ebi.ac.uk/api/annotations"
protein_uniprot_id = "P02100" # ID de UniProt de la proteína a consultar
annotation_type = "MUTAGEN"

# --- NUEVA FUNCIÓN: Obtener el nombre de la proteína de UniProt ---
def get_protein_name(uniprot_id):
    """
    Obtiene el nombre recomendado de una proteína desde la API de UniProt.
    """
    uniprot_api_url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    try:
        response = requests.get(uniprot_api_url, headers={"Accept": "application/json"})
        response.raise_for_status() # Lanza un error para respuestas 4xx/5xx

        data = response.json()
        
        # El nombre recomendado suele estar en la sección 'proteinDescription' -> 'recommendedName' -> 'fullName'
        # o 'alternativeNames' si no hay recomendado.
        # Puede variar un poco la estructura, así que hay que ser robusto.
        if 'proteinDescription' in data and 'recommendedName' in data['proteinDescription'] and \
           'fullName' in data['proteinDescription']['recommendedName']:
            return data['proteinDescription']['recommendedName']['fullName']['value']
        elif 'proteinDescription' in data and 'alternativeNames' in data['proteinDescription'] and \
             len(data['proteinDescription']['alternativeNames']) > 0 and \
             'fullName' in data['proteinDescription']['alternativeNames'][0]:
            return data['proteinDescription']['alternativeNames'][0]['fullName']['value']
        elif 'proteinDescription' in data and 'submittedNames' in data['proteinDescription'] and \
             len(data['proteinDescription']['submittedNames']) > 0 and \
             'fullName' in data['proteinDescription']['submittedNames'][0]:
            return data['proteinDescription']['submittedNames'][0]['fullName']['value']
        else:
            return f"Nombre Desconocido ({uniprot_id})" # Si no encuentra el nombre
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener el nombre de UniProt para {uniprot_id}: {e}")
        return f"Error al Cargar Nombre ({uniprot_id})"
    except Exception as e:
        print(f"Error inesperado al parsear nombre de UniProt para {uniprot_id}: {e}")
        return f"Error al Cargar Nombre ({uniprot_id})"

# --- Obtener el nombre de la proteína al inicio ---
protein_name = get_protein_name(protein_uniprot_id)
print(f"Nombre de la proteína: {protein_name}")


print(f"Obteniendo datos de AlphaMissense para UniProt ID: {protein_uniprot_id}")

try:
    request_url = f"{BASE_ANNOTATIONS_URL}/{protein_uniprot_id}"
    params = {
        "annotation_type": annotation_type
    }

    response = requests.get(request_url, params=params)
    response.raise_for_status()

    raw_api_data = response.json()

    # --- Acceder a la lista de scores: Nivel 2 de anidamiento ---
    if 'annotation' in raw_api_data and isinstance(raw_api_data['annotation'], list) and len(raw_api_data['annotation']) > 0:
        annotation_details = raw_api_data['annotation'][0]
        
        if 'regions' in annotation_details and isinstance(annotation_details['regions'], list) and len(annotation_details['regions']) > 0:
            scores_list = annotation_details['regions'][0].get('annotation_value')

            if scores_list and isinstance(scores_list, list):
                df_heatmap = pd.DataFrame({'score': scores_list})
                df_heatmap['pos'] = range(1, len(scores_list) + 1)
                
                print("\n--- DataFrame de Pandas Creado Exitosamente ---")
                print(f"Dimensiones del DataFrame: {df_heatmap.shape} (filas, columnas)")
                print("\nPrimeras 5 filas del DataFrame:")
                print(df_heatmap.head())

                print("\nColumnas disponibles en el DataFrame:")
                print(df_heatmap.columns)

                csv_filename = f"{protein_uniprot_id}_{protein_name}_scores.csv"
                df_heatmap.to_csv(csv_filename, index=False)
                print(f"\nDatos guardados en '{csv_filename}'")

                if 'score' in df_heatmap.columns:
                    print("\nEstadísticas descriptivas de la columna 'score':")
                    print(df_heatmap['score'].describe())
                    
                    patogenic_threshold = 0.564
                    benign_threshold = 0.34

                    num_patogenic = df_heatmap[df_heatmap['score'] > patogenic_threshold].shape[0]
                    num_benign = df_heatmap[df_heatmap['score'] < benign_threshold].shape[0]
                    num_uncertain = df_heatmap[(df_heatmap['score'] >= benign_threshold) & (df_heatmap['score'] <= patogenic_threshold)].shape[0]

                    print(f"\nRecuento de posiciones por categoría (usando umbrales de ejemplo):")
                    print(f"  - Patogénicas (> {patogenic_threshold}): {num_patogenic}")
                    print(f"  - Benignas (< {benign_threshold}): {num_benign}")
                    print(f"  - Inciertas ({benign_threshold}-{patogenic_threshold}): {num_uncertain}")
                else:
                    print(f"\nAdvertencia: La columna 'score' no se encontró. Revise los datos.")
            else:
                print("Error: 'annotation_value' no es una lista o está vacía.")
        else:
            print("Error: La clave 'regions' no se encontró o no es una lista válida.")
    else:
        print("Error: La clave 'annotation' no se encontró, no es una lista o está vacía.")
        print("Estructura completa de la respuesta JSON (para depuración):")
        print(json.dumps(raw_api_data, indent=2))

except requests.exceptions.HTTPError as errh:
    print(f"Error HTTP: {errh}")
    print(f"Respuesta del servidor: {errh.response.text}")
except requests.exceptions.ConnectionError as errc:
    print(f"Error de conexión: {errc}")
except requests.exceptions.Timeout as errt:
    print(f"Tiempo de espera agotado: {errt}")
except requests.exceptions.RequestException as err:
    print(f"Ocurrió un error al realizar la solicitud: {err}")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")


# --- Visualizaciones (ahora usan protein_name) ---

# Histograma de Scores
if 'score' in df_heatmap.columns:
    plt.figure(figsize=(10, 6))
    sns.histplot(df_heatmap['score'], bins=20, kde=True, color='skyblue')
    plt.title(f'Distribución de Scores de Patogenicidad para {protein_name} ({protein_uniprot_id})') # Título con nombre
    plt.xlabel('Score de Patogenicidad (0-1)')
    plt.ylabel('Frecuencia de Posiciones')
    plt.axvline(x=0.564, color='r', linestyle='--', label='Umbral Patogénico (>0.564)')
    plt.axvline(x=0.34, color='b', linestyle='--', label='Umbral Benigno (<0.34)')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()
else:
    print("La columna 'score' no está disponible para el histograma.")


# Scatter Plot con Color por Categoría
# Definir umbrales (se repiten, pero es seguro tenerlos en este bloque también si el try/except anterior falla)
patogenic_threshold = 0.564
benign_threshold = 0.34

def assign_category(score):
    if score > patogenic_threshold:
        return 'Likely Pathogenic'
    elif score < benign_threshold:
        return 'Likely Benign'
    else:
        return 'Uncertain'

if 'score' in df_heatmap.columns:
    df_heatmap['category'] = df_heatmap['score'].apply(assign_category)

    plt.figure(figsize=(18, 7))
    sns.scatterplot(x='pos', y='score', hue='category', data=df_heatmap,
                    palette={'Likely Pathogenic': 'red', 'Uncertain': 'orange', 'Likely Benign': 'blue'},
                    s=20, alpha=0.7)
    
    plt.title(f'Scores de Patogenicidad por Posición (Categorizado) para {protein_name} ({protein_uniprot_id})') # Título con nombre
    plt.xlabel('Posición del Aminoácido')
    plt.ylabel('Score de Patogenicidad')
    plt.axhline(y=patogenic_threshold, color='r', linestyle='--', label='Umbral Patogénico')
    plt.axhline(y=benign_threshold, color='b', linestyle='--', label='Umbral Benigno')
    plt.legend(title='Categoría')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()
else:
    print("La columna 'score' no está disponible para la categorización.")