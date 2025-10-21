# ===========================================
# SECCIÓN 3: CÁLCULO DE RMSD Y ANÁLISIS ESTRUCTURAL
# PyMOL Script para Análisis Comparativo de Estructuras
# ===========================================

# Cargar las estructuras PDB
load original.pdb, original
load mutante.pdb, mutante

# Mostrar como cartoon
show cartoon, all

# Colorear para distinguir
color cyan, original
color magenta, mutante

# Ocultar todo inicialmente
hide all

# Mostrar solo cartoon
show cartoon, all

# Centrar vista
center all

# Zoom apropiado
zoom all, 10

# Alinear las estructuras usando átomos C-alpha
# El comando align calcula RMSD automáticamente
align mutante, original

# Mostrar también como sticks los residuos mutados (ejemplo: posición 50)
# select mut_site, (resi 50) and (original or mutante)
# show sticks, mut_site
# color red, mut_site

# Calcular distancia entre residuos específicos si es necesario
# distance mut_dist, original///50/CA, mutante///50/CA

# Guardar la alineación superpuesta
# save superposed_structures.pdb, all

print "==========================================="
print "ANÁLISIS COMPLETADO"
print "==========================================="
print "Estructuras cargadas: original.pdb y mutante.pdb"
print "Alineación completada usando átomos C-alpha"
print "RMSD calculado automáticamente por el comando align"
print "==========================================="
