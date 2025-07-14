#!/bin/bash
# Script simple - alternatio a Makefile

set -euo pipefail

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_PATH="${REPO_PATH:-$SCRIPT_DIR}"
VERBOSE="${VERBOSE:-false}"

# Colores para salida
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Ejecución principal
main() {
    log "Iniciando pipeline de análisis de repositorio."
    
    # Paso 1: Análisis de gráfico
    log "Paso 1: Análisis de gráfico"
    if [[ "$VERBOSE" == "true" ]]; then
        python3 src/graph_analysis.py --repo "$REPO_PATH" --output metrics.json --verbose
    else
        python3 src/graph_analysis.py --repo "$REPO_PATH" --output metrics.json
    fi
    success "Analisis de gráfico completado. Métricas guardadas en metrics.json"
    
    # Paso 2: Generar reporte Markdown
    log "Paso 2: Generación de reporte Markdown"
    if [[ "$VERBOSE" == "true" ]]; then
        python3 src/report_suite.py --format md --input metrics.json --output report.md --repo "$REPO_PATH" --verbose
    else
        python3 src/report_suite.py --format md --input metrics.json --output report.md --repo "$REPO_PATH"
    fi
    success "Reporte Markdown generado: report.md"

}


# Comandos de ayuda
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Función principal ejecutada
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi