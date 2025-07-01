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

# --- FUNCIÓN REUTILIZADA: Obtener el nombre de la proteína de UniProt ---
def get_protein_name(uniprot_id):
    """
    Obtiene el nombre recomendado de una proteína desde la API de UniProt.
    """
    uniprot_api_url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    try:
        response = requests.get(uniprot_api_url, headers={"Accept": "application/json"})
        response.raise_for_status()

        data = response.json()
        
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
            return f"Nombre Desconocido ({uniprot_id})"
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener el nombre de UniProt para {uniprot_id}: {e}")
        return f"Error al Cargar Nombre ({uniprot_id})"
    except Exception as e:
        print(f"Error inesperado al parsear nombre de UniProt para {uniprot_id}: {e}")
        return f"Error al Cargar Nombre ({uniprot_id})"

# --- FUNCIÓN REUTILIZADA: Obtener la secuencia de la proteína de UniProt ---
def get_protein_sequence(uniprot_id):
    """
    Obtiene la secuencia de aminoácidos de una proteína desde la API de UniProt.
    """
    uniprot_api_url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    try:
        response = requests.get(uniprot_api_url, headers={"Accept": "application/json"})
        response.raise_for_status()

        data = response.json()
        
        if 'sequence' in data and 'value' in data['sequence']:
            return data['sequence']['value']
        else:
            print(f"Advertencia: No se encontró la secuencia para {uniprot_id}.")
            return ""
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener la secuencia de UniProt para {uniprot_id}: {e}")
        return ""
    except Exception as e:
        print(f"Error inesperado al parsear secuencia de UniProt para {uniprot_id}: {e}")
        return ""


# --- Obtener el nombre y la secuencia de la proteína al inicio ---
protein_name = get_protein_name(protein_uniprot_id)
protein_sequence = get_protein_sequence(protein_uniprot_id)

print(f"Nombre de la proteína: {protein_name}")
print(f"Longitud de la secuencia de la proteína: {len(protein_sequence)}")

# Validar que la secuencia no esté vacía
if not protein_sequence:
    print("ERROR: No se pudo obtener la secuencia de la proteína. No se puede continuar con el análisis de residuos.")
    exit() # Sale del script si no hay secuencia


print(f"\nObteniendo datos de AlphaMissense para UniProt ID: {protein_uniprot_id}")

df_heatmap = pd.DataFrame() # Inicializar como DataFrame vacío para asegurar que exista

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
                min_len = min(len(scores_list), len(protein_sequence))
                
                if len(scores_list) != len(protein_sequence):
                    print(f"Advertencia: La longitud de los scores ({len(scores_list)}) no coincide con la longitud de la secuencia ({len(protein_sequence)}).")
                    print(f"Se truncarán ambos al mínimo de longitud: {min_len}.")
                    scores_list = scores_list[:min_len]
                    protein_sequence = protein_sequence[:min_len]

                df_heatmap = pd.DataFrame({
                    'pos': range(1, min_len + 1),
                    'amino_acid': list(protein_sequence),
                    'score': scores_list
                })
                
                print("\n--- DataFrame de Pandas Creado Exitosamente ---")
                print(f"Dimensiones del DataFrame: {df_heatmap.shape} (filas, columnas)")
                print("\nPrimeras 5 filas del DataFrame:")
                print(df_heatmap.head())

                print("\nColumnas disponibles en el DataFrame:")
                print(df_heatmap.columns)

                csv_filename = f"{protein_uniprot_id}_{protein_name.replace(' ', '_').replace('/', '_')}_AlphaMissense_scores.csv"
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
                    print(f"  - Patogénicas (> {patogenic_threshold}): {num_patogenic}")
                    print(f"  - Benignas (< {benign_threshold}): {num_benign}")
                    print(f"  - Inciertas ({benign_threshold}-{patogenic_threshold}): {num_uncertain}")
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


# --- Visualizaciones ---

# Histograma de Scores
if not df_heatmap.empty and 'score' in df_heatmap.columns:
    plt.figure(figsize=(10, 6))
    sns.histplot(df_heatmap['score'], bins=20, kde=True, color='skyblue')
    plt.title(f'Distribución de Scores de Patogenicidad para {protein_name} ({protein_uniprot_id})')
    plt.xlabel('Score de Patogenicidad (0-1)')
    plt.ylabel('Frecuencia de Posiciones')
    
    patogenic_threshold = 0.564
    benign_threshold = 0.34
    plt.axvline(x=patogenic_threshold, color='r', linestyle='--', label='Umbral Patogénico (>0.564)')
    plt.axvline(x=benign_threshold, color='b', linestyle='--', label='Umbral Benigno (<0.34)')
    
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()
else:
    print("La columna 'score' no está disponible para el histograma o el DataFrame está vacío.")


# Scatter Plot con Color por Categoría Y ETIQUETA DE AMINOÁCIDO
# Definir umbrales
patogenic_threshold = 0.564
benign_threshold = 0.34

def assign_category(score):
    if score > patogenic_threshold:
        return 'Likely Pathogenic'
    elif score < benign_threshold:
        return 'Likely Benign'
    else:
        return 'Uncertain'

if not df_heatmap.empty and 'score' in df_heatmap.columns:
    df_heatmap['category'] = df_heatmap['score'].apply(assign_category)

    plt.figure(figsize=(20, 8)) # Aumentamos el tamaño de la figura para el texto
    ax = sns.scatterplot(x='pos', y='score', hue='category', data=df_heatmap,
                         palette={'Likely Pathogenic': 'red', 'Uncertain': 'orange', 'Likely Benign': 'blue'},
                         s=50, alpha=0.7, # Aumentamos el tamaño de los puntos
                         legend='full') # Aseguramos que la leyenda se muestre
    
    # --- Añadir el símbolo del aminoácido a cada punto ---
    # Iteramos sobre las filas del DataFrame para añadir texto
    for line in range(0, df_heatmap.shape[0]):
        # Solo etiquetamos si el score es relevante o si queremos ver todos los AA
        # Por ahora, etiquetamos todos. Si el gráfico se satura, podemos añadir una condición.
        ax.text(df_heatmap['pos'][line]+0.2, df_heatmap['score'][line], # Posición del texto (ligeramente desplazado)
                df_heatmap['amino_acid'][line], # Texto a mostrar (el aminoácido)
                horizontalalignment='left', size='small', color='black', weight='semibold') # Estilo del texto


    plt.title(f'Scores de Patogenicidad por Posición (Categorizado con AA) para {protein_name} ({protein_uniprot_id})')
    plt.xlabel('Posición del Aminoácido')
    plt.ylabel('Score de Patogenicidad')
    plt.axhline(y=patogenic_threshold, color='r', linestyle='--', label='Umbral Patogénico')
    plt.axhline(y=benign_threshold, color='b', linestyle='--', label='Umbral Benigno')
    plt.legend(title='Categoría')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()
else:
    print("La columna 'score' no está disponible para la categorización o el DataFrame está vacío.")