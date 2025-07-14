#!/bin/bash
# Script para crear un mini repositorio de prueba

# Crear directorio temporal si no existe
REPO_DIR="fixtures/mini_repo"
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"

# Limpiar si ya existe
rm -rf .git
rm -f *.txt

# Inicializar repositorio
git init

# Configurar usuario para el repo
git config user.name "Test User"
git config user.email "test@example.com"

# Crear commits secuenciales
echo "Contenido Inicial" > file1.txt
git add file1.txt
git commit -m "Commit inicial"
git tag v0.0.0

echo "Segunda linea" >> file1.txt
git add file1.txt
git commit -m "Añade una segunda línea"

# Crear branch y merge
git checkout -b feature-branch
echo "Contenido feature" > feature.txt
git add feature.txt
git commit -m "Añade feature"

echo "Más contenido en feature" >> feature.txt
git add feature.txt
git commit -m "Modifica feature"

# Volver a main y hacer merge
git checkout main
echo "Main development" > main.txt
git add main.txt
git commit -m "Main development"

# Merge (esto creará un merge commit)
git merge feature-branch -m "Merge feature branch"

# Algunos commits más
echo "Post merge" >> file1.txt
git add file1.txt
git commit -m "Post-merge modificacion"

# Crear otro branch para más complejidad
git checkout -b hotfix
echo "Fix critico" > hotfix.txt
git add hotfix.txt
git commit -m "Hotfix critico"

git checkout main
git merge hotfix -m "Merge hotfix"

echo "Mini repository creado satisfactoriamente."
git log --oneline --graph --all