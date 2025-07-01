import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# IMPORTACIONES PARA BIOPYTHON
from Bio.PDB import MMCIFParser
from Bio.PDB.PDBParser import PDBParser # Por si el archivo es PDB
import numpy as np # Para el promedio si fuera necesario, aunque Pandas lo hace


# --- Configuración de la API ---
BASE_PREDICTION_URL = "https://alphafold.ebi.ac.uk/api/prediction"
protein_uniprot_id = "P02100" 

# --- Función para obtener el nombre de la proteína ---
def get_protein_name(uniprot_id):
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

# --- Obtener el nombre de la proteína al inicio ---
protein_name = get_protein_name(protein_uniprot_id)
print(f"Nombre de la proteína: {protein_name}")

print(f"\n--- FASE 1: Obteniendo la URL del archivo CIF/PDB para {protein_uniprot_id} ---")

cif_download_url = None 
downloaded_file_name = None 

try:
    request_url = f"{BASE_PREDICTION_URL}/{protein_uniprot_id}"
    response = requests.get(request_url)
    response.raise_for_status()

    prediction_data = response.json()

    if isinstance(prediction_data, list) and len(prediction_data) > 0:
        first_model_data = prediction_data[0] 

        if 'cifUrl' in first_model_data and first_model_data['cifUrl']:
            cif_download_url = first_model_data['cifUrl']
            print(f"\nURL del archivo CIF del modelo encontrada:")
            print(f"  {cif_download_url}")
        else:
            print("\nNo se encontró una URL de archivo CIF directo. Buscando alternativas...")
            if 'pdbUrl' in first_model_data and first_model_data['pdbUrl']: 
                cif_download_url = first_model_data['pdbUrl']
                print(f"  Encontrada URL PDB: {first_model_data['pdbUrl']}")
            elif 'bcifUrl' in first_model_data and first_model_data['bcifUrl']:
                print(f"  Encontrada URL bcif: {first_model_data['bcifUrl']}")
                print("Nota: El formato .bcif es binario y requiere librerías específicas para parsear. No se usará en este script.")
            else:
                 print("No se encontró ninguna URL de archivo CIF/PDB/bcif en la respuesta del modelo.")
                 print("Estructura de datos del primer modelo (para depuración):")
                 print(json.dumps(first_model_data, indent=2))
    else:
        print("La respuesta de la API para la predicción del modelo no es una lista o está vacía.")
        print("Estructura completa de la respuesta JSON (para depuración):")
        print(json.dumps(prediction_data, indent=2))

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

# --- FASE 2: Descargar el contenido del archivo CIF/PDB ---
cif_content = None 

if cif_download_url:
    downloaded_file_name = cif_download_url.split('/')[-1] 
    print(f"\n--- FASE 2: Descargando el contenido de {downloaded_file_name} ---")
    try:
        file_response = requests.get(cif_download_url)
        file_response.raise_for_status()
        cif_content = file_response.text 
        
        with open(downloaded_file_name, 'w') as f:
            f.write(cif_content)
        print(f"\nArchivo '{downloaded_file_name}' guardado localmente para revisión.")

        print("\nContenido del archivo descargado exitosamente. Primeras 20 líneas:")
        for i, line in enumerate(cif_content.splitlines()):
            if i >= 20:
                break
            print(line)
        
    except requests.exceptions.HTTPError as errh:
        print(f"Error HTTP al descargar el archivo: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error de conexión al descargar el archivo: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Tiempo de espera agotado al descargar el archivo: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Ocurrió un error al descargar el archivo: {err}")
    except Exception as e:
        print(f"Ocurrió un error inesperado al manejar el archivo: {e}")
else:
    print("\nNo se pudo obtener una URL de descarga válida para proceder con la Fase 2.")

# --- FASE 3: Parsear el contenido del archivo para extraer los valores pLDDT usando Biopython ---
plddt_data = {} 
df_plddt = None 

if downloaded_file_name and os.path.exists(downloaded_file_name):
    print(f"\n--- FASE 3: Parseando el contenido de {downloaded_file_name} para pLDDT usando Biopython ---")
    
    if downloaded_file_name.endswith('.cif'):
        try:
            print("Intentando parsear con Biopython MMCIFParser...")
            parser = MMCIFParser()
            structure = parser.get_structure("protein_model", downloaded_file_name)
            
            plddt_scores_by_residue = {}

            # Recorrer la estructura para extraer pLDDT
            for model in structure:
                for chain in model:
                    for residue in chain:
                        # Biopython guarda el factor B (pLDDT) en atom.bfactor
                        residue_plddt_values = []
                        for atom in residue:
                            # AlphaFold almacena el pLDDT en el campo 'bfactor'
                            residue_plddt_values.append(atom.bfactor)
                        
                        if residue_plddt_values:
                            # Calcular el promedio de pLDDT para el residuo
                            avg_plddt = sum(residue_plddt_values) / len(residue_plddt_values)
                            # Usamos el id del residuo para la posición
                            # residue.id[1] es el número de secuencia (seqid.num en gemmi)
                            plddt_scores_by_residue[residue.id[1]] = avg_plddt 

            if plddt_scores_by_residue:
                df_plddt = pd.DataFrame(plddt_scores_by_residue.items(), columns=['pos', 'plddt_score'])
                df_plddt = df_plddt.sort_values(by='pos').reset_index(drop=True)
                
                print("\nDataFrame de pLDDT REALES creado exitosamente a partir de archivo CIF usando Biopython.")
                print(f"Dimensiones del DataFrame: {df_plddt.shape} (filas, columnas)")
                print("\nPrimeras 5 filas del DataFrame:")
                print(df_plddt.head())
            else:
                print("\nNo se pudieron extraer scores pLDDT usando Biopython (quizás no hay datos atómicos).")
                df_plddt = None

        except Exception as e:
            print(f"\nError al parsear el archivo CIF con Biopython: {e}")
            df_plddt = None
            
    elif downloaded_file_name.endswith('.pdb'):
        try:
            print("Intentando parsear con Biopython PDBParser...")
            parser = PDBParser()
            structure = parser.get_structure("protein_model", downloaded_file_name)
            
            plddt_scores_by_residue = {}
            for model in structure:
                for chain in model:
                    for residue in chain:
                        residue_plddt_values = []
                        for atom in residue:
                            residue_plddt_values.append(atom.bfactor)
                        if residue_plddt_values:
                            avg_plddt = sum(residue_plddt_values) / len(residue_plddt_values)
                            plddt_scores_by_residue[residue.id[1]] = avg_plddt
            
            if plddt_scores_by_residue:
                df_plddt = pd.DataFrame(plddt_scores_by_residue.items(), columns=['pos', 'plddt_score'])
                df_plddt = df_plddt.sort_values(by='pos').reset_index(drop=True)
                print("\nDataFrame de pLDDT REALES creado exitosamente a partir de archivo PDB usando Biopython.")
                print(f"Dimensiones del DataFrame: {df_plddt.shape} (filas, columnas)")
                print("\nPrimeras 5 filas del DataFrame:")
                print(df_plddt.head())
            else:
                print("\nNo se pudieron extraer scores pLDDT de PDB usando Biopython.")
                df_plddt = None
        except Exception as e:
            print(f"\nError al parsear el archivo PDB con Biopython: {e}")
            df_plddt = None
    else:
        print("\nFormato de archivo no reconocido para extraer pLDDT (no es .cif ni .pdb).")
        df_plddt = None
else:
    print("\nEl archivo CIF/PDB no fue descargado o no existe para la Fase 3.")
    df_plddt = None


# --- FASE 4: Visualización de la Confianza pLDDT con datos reales ---
if df_plddt is not None and 'plddt_score' in df_plddt.columns and 'pos' in df_plddt.columns:
    print("\n--- FASE 4: Generando Visualización de Confianza pLDDT ---")
    # Umbrales pLDDT
    high_confidence_threshold = 90
    good_confidence_threshold = 70
    low_confidence_threshold = 50

    def assign_plddt_category(score):
        if score > high_confidence_threshold:
            return 'Very High'
        elif score > good_confidence_threshold:
            return 'High'
        elif score > low_confidence_threshold:
            return 'Low'
        else:
            return 'Very Low'

    df_plddt['confidence_category'] = df_plddt['plddt_score'].apply(assign_plddt_category)

    category_order = ['Very High', 'High', 'Low', 'Very Low']
    plddt_palette = {
        'Very High': 'darkblue',
        'High': 'skyblue',
        'Low': 'orange',
        'Very Low': 'red'
    }

    plt.figure(figsize=(18, 7))
    sns.scatterplot(x='pos', y='plddt_score', hue='confidence_category', data=df_plddt,
                    palette=plddt_palette,
                    hue_order=category_order,
                    s=20, alpha=0.7)
    
    plt.title(f'Confianza del Modelo (pLDDT) por Posición para {protein_name} ({protein_uniprot_id})')
    plt.xlabel('Posición del Aminoácido')
    plt.ylabel('pLDDT Score (0-100)')
    plt.axhline(y=high_confidence_threshold, color='darkblue', linestyle='--', label=f'Muy Alta Confianza (> {high_confidence_threshold})')
    plt.axhline(y=good_confidence_threshold, color='skyblue', linestyle='--', label=f'Alta Confianza (> {good_confidence_threshold})')
    plt.axhline(y=low_confidence_threshold, color='orange', linestyle='--', label=f'Baja Confianza (> {low_confidence_threshold})')
    plt.legend(title='Confianza de Predicción')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(0, 100)
    plt.show()
else:
    print("\nNo se pudo crear el DataFrame de pLDDT REALES o faltan columnas para la visualización.")