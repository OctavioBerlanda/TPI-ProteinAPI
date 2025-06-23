import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ¡NUEVAS IMPORTACIONES PARA BIOPYTHON!
from Bio.PDB import MMCIFParser
from Bio.PDB.PDBParser import PDBParser # Por si el archivo es PDB
import numpy as np # Necesario para el pLDDT

# --- Configuración de la API ---
BASE_PREDICTION_URL = "https://alphafold.ebi.ac.uk/api/prediction"
# Puedes cambiar este ID para probar diferentes proteínas
protein_uniprot_id = "P02100" # Hemoglobina subunidad Épsilon

# --- Función para obtener información detallada de la proteína de UniProt ---
def get_protein_info(uniprot_id):
    uniprot_api_url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    protein_info = {
        'uniprot_id': uniprot_id, 
        'name': f"Nombre Desconocido ({uniprot_id})",
        'sequence': None,
        'sequence_length': None,
        'mass_kDa': None 
    }
    
    try:
        response = requests.get(uniprot_api_url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()
        
        # Extraer nombre
        if 'proteinDescription' in data and 'recommendedName' in data['proteinDescription'] and \
           'fullName' in data['proteinDescription']['recommendedName']:
            protein_info['name'] = data['proteinDescription']['recommendedName']['fullName']['value']
        elif 'proteinDescription' in data and 'alternativeNames' in data['proteinDescription'] and \
             len(data['proteinDescription']['alternativeNames']) > 0 and \
             'fullName' in data['proteinDescription']['alternativeNames'][0]:
            protein_info['name'] = data['proteinDescription']['alternativeNames'][0]['fullName']['value']
        elif 'proteinDescription' in data and 'submittedNames' in data['proteinDescription'] and \
             len(data['proteinDescription']['submittedNames']) > 0 and \
             'fullName' in data['proteinDescription']['submittedNames'][0]:
            protein_info['name'] = data['proteinDescription']['submittedNames'][0]['fullName']['value']

        # Extraer secuencia
        if 'sequence' in data and 'value' in data['sequence']:
            protein_info['sequence'] = data['sequence']['value']
            protein_info['sequence_length'] = len(protein_info['sequence'])
        
        # Extraer masa molecular
        if 'sequence' in data and 'molWeight' in data['sequence']:
            protein_info['mass_kDa'] = data['sequence']['molWeight'] / 1000.0 # Convertir a kDa
        
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener información de UniProt para {uniprot_id}: {e}")
    except Exception as e:
        print(f"Error inesperado al parsear información de UniProt para {uniprot_id}: {e}")
    
    return protein_info

# --- Obtener información de la proteína al inicio ---
protein_info = get_protein_info(protein_uniprot_id)
protein_name = protein_info['name']
protein_sequence = protein_info['sequence']
protein_sequence_length = protein_info['sequence_length']
protein_mass_kDa = protein_info['mass_kDa']

print(f"Nombre de la proteína: {protein_name}")
if protein_sequence:
    print(f"Longitud de la secuencia: {protein_sequence_length} aminoácidos")
    print(f"Peso Molecular Aproximado: {protein_mass_kDa:.2f} kDa" if protein_mass_kDa else "N/A")
    print(f"Secuencia (primeros 50 y últimos 50 caracteres):")
    # Para manejar secuencias cortas que no tienen 100+ caracteres
    display_sequence = protein_sequence
    if len(display_sequence) > 100:
        print(f"  {display_sequence[:50]}...{display_sequence[-50:]}")
    else:
        print(f"  {display_sequence}")
else:
    print("Secuencia de aminoácidos no disponible de UniProt.")

# --- Guardar toda la información de la proteína en un archivo JSON (¡Modificado!) ---
output_json_file_name = f"{protein_uniprot_id}_protein_data.json"
try:
    # Asegúrate de que el diccionario protein_info tiene la secuencia completa
    # y cualquier otro dato que quieras en el JSON.
    # El diccionario 'protein_info' ya contiene todo lo que necesitamos.
    with open(output_json_file_name, 'w', encoding='utf-8') as f:
        json.dump(protein_info, f, indent=4, ensure_ascii=False)
    print(f"\nDatos completos de la proteína (incluyendo secuencia) guardados en '{output_json_file_name}'.")
except Exception as e:
    print(f"Error al guardar los datos en '{output_json_file_name}': {e}")


print(f"\n--- FASE 1: Obteniendo las URLs de los archivos CIF/PDB para {protein_uniprot_id} ---")

cif_download_url = None 
downloaded_cif_file_name = None
first_model_data = None 

try:
    request_url = f"{BASE_PREDICTION_URL}/{protein_uniprot_id}"
    response = requests.get(request_url)
    response.raise_for_status()

    prediction_data = response.json()

    if isinstance(prediction_data, list) and len(prediction_data) > 0:
        first_model_data = prediction_data[0] 

        # Obtener URL del CIF/PDB
        if 'cifUrl' in first_model_data and first_model_data['cifUrl']:
            cif_download_url = first_model_data['cifUrl']
            print(f"\nURL del archivo CIF del modelo encontrada:")
            print(f"   {cif_download_url}")
        else:
            print("\nNo se encontró una URL de archivo CIF directo. Buscando alternativas...")
            if 'pdbUrl' in first_model_data and first_model_data['pdbUrl']: 
                cif_download_url = first_model_data['pdbUrl']
                print(f"   Encontrada URL PDB: {first_model_data['pdbUrl']}")
            elif 'bcifUrl' in first_model_data and first_model_data['bcifUrl']:
                print(f"   Encontrada URL bcif: {first_model_data['bcifUrl']}")
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
    print(f"Ocurrió un error inesperado en la Fase 1: {e}")

# --- FASE 1.5: Resumen de datos del modelo desde la API ---
if first_model_data:
    print(f"\n--- FASE 1.5: Resumen de datos del modelo desde la API para {protein_uniprot_id} ---")
    print(f"  ID de UniProt: {first_model_data.get('uniprotId', 'N/A')}")
    print(f"  ID del Modelo AlphaFold: {first_model_data.get('modelId', 'N/A')}")
    print(f"  Tipo de Modelo: {first_model_data.get('modelType', 'N/A')}")
    print(f"  Fecha de Generación/Actualización: {first_model_data.get('date', 'N/A')}")
    print(f"  pLDDT Promedio del Modelo: {first_model_data.get('plddt', 'N/A'):.2f}" if isinstance(first_model_data.get('plddt'), (int, float)) else f"  pLDDT Promedio del Modelo: {first_model_data.get('plddt', 'N/A')}")
else:
    print("\n--- FASE 1.5: No hay datos de modelo disponibles para resumir. ---")


# --- FASE 2: Descargando el contenido del archivo CIF/PDB ---
cif_content = None 

if cif_download_url:
    downloaded_cif_file_name = cif_download_url.split('/')[-1] 
    print(f"\n--- FASE 2: Descargando el contenido de {downloaded_cif_file_name} ---")
    try:
        file_response = requests.get(cif_download_url)
        file_response.raise_for_status()
        cif_content = file_response.text 
        
        with open(downloaded_cif_file_name, 'w') as f:
            f.write(cif_content)
        print(f"\nArchivo '{downloaded_cif_file_name}' guardado localmente.")

        print("\nContenido del archivo descargado exitosamente. Primeras 20 líneas:")
        for i, line in enumerate(cif_content.splitlines()):
            if i >= 20:
                break
            print(line)
        
    except requests.exceptions.HTTPError as errh:
        print(f"Error HTTP al descargar el archivo CIF: {errh}")
        downloaded_cif_file_name = None 
    except requests.exceptions.ConnectionError as errc:
        print(f"Error de conexión al descargar el archivo CIF: {errc}")
        downloaded_cif_file_name = None
    except requests.exceptions.Timeout as errt:
        print(f"Tiempo de espera agotado al descargar el archivo CIF: {errt}")
        downloaded_cif_file_name = None
    except requests.exceptions.RequestException as err:
        print(f"Ocurrió un error al descargar el archivo CIF: {err}")
        downloaded_cif_file_name = None
    except Exception as e:
        print(f"Ocurrió un error inesperado al manejar el archivo CIF: {e}")
        downloaded_cif_file_name = None
else:
    print("\nNo se pudo obtener una URL de descarga válida para el archivo CIF/PDB. No se descargará.")


# --- FASE 3.1: Parseando pLDDT de CIF/PDB ---
plddt_data = {} 
df_plddt = None 

if downloaded_cif_file_name and os.path.exists(downloaded_cif_file_name):
    print(f"\n--- FASE 3.1: Parseando pLDDT de {downloaded_cif_file_name} usando Biopython ---")
    
    if downloaded_cif_file_name.endswith('.cif'):
        try:
            print("Intentando parsear con Biopython MMCIFParser...")
            parser = MMCIFParser()
            structure = parser.get_structure("protein_model", downloaded_cif_file_name)
            
            plddt_scores_by_residue = {}
            for model in structure:
                for chain in model:
                    for residue in chain:
                        residue_plddt_values = []
                        for atom in residue:
                            if hasattr(atom, 'bfactor'):
                                residue_plddt_values.append(atom.bfactor)
                        
                        if residue_plddt_values:
                            avg_plddt = sum(residue_plddt_values) / len(residue_plddt_values)
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
            print(f"\nError al parsear el archivo CIF con Biopython para pLDDT: {e}")
            df_plddt = None
            
    elif downloaded_cif_file_name.endswith('.pdb'):
        try:
            print("Intentando parsear con Biopython PDBParser...")
            parser = PDBParser()
            structure = parser.get_structure("protein_model", downloaded_cif_file_name)
            
            plddt_scores_by_residue = {}
            for model in structure:
                for chain in model:
                    for residue in chain:
                        residue_plddt_values = []
                        for atom in residue:
                            if hasattr(atom, 'bfactor'):
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
        print("\nFormato de archivo de modelo no reconocido para extraer pLDDT (no es .cif ni .pdb).")
        df_plddt = None
else:
    print("\nEl archivo CIF/PDB no fue descargado o no existe para la extracción de pLDDT.")


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
