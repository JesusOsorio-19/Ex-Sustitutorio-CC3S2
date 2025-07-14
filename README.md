# Ex-Sustitutorio-CC3S2

## Sistema de análisis offline de repositorios Git usando algoritmos de grafos y micro-servicios

### Propósito

Esta herramienta implementa un sistema completo de análisis de repositorios Git que:

- **Analiza la estructura del DAG de commits** usando algoritmos de grafos (NetworkX).
- **Calcula métricas avanzadas**: densidad de ramas, ruta crítica de merges, entropía histórica.
- **Genera reportes** en Markdown usando patrones de diseño (DI, Facade, Composition).
- **Funciona completamente offline** sin conectividad externa.
- **Incluye CI/CD offline** con GitHub Actions.

### Instalación offline 

```bash
# Clonamos el repo
git clone <repo-url>
cd <repo>

# Crear entorno virtual
python -m venv venv
source venv\Scripts\activate   # Windows

# Instalar dependencias offline (si se tiene cache pip)
pip install --no-index --find-links ./wheels -r requirements.txt

# O de forma online
pip install -r requirements.txt


# Por último onfigurar scripts, dar permisos de ejecución
chmod +x run.sh
chmod +x scripts/make_report.sh
```




