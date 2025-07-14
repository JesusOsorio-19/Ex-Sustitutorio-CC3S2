import json
import argparse
import subprocess
import re
import math
from typing import Dict, List, Tuple, Any, Set, Optional
from pathlib import Path
from collections import defaultdict, deque
import networkx as nx



class GitGraphAnalyzer:
    """Analiza la estructura del gráfico de commits del repositorio de Git."""
    
    def __init__(self, repo_path: str):
        """Inicializar el analizador con la ruta del repositorio."""
        self.repo_path = Path(repo_path)
        self.graph = nx.DiGraph()
        self.commits = {} # commit_hash -> commit_info
        self.metrics = {}
        self.levels = {} # commit -> level (distancia desde la raíz)
    
    def load_git_data(self) -> None:
        """Cargar datos de confirmación de Git y compilar DAG."""
        try:
            # Obtener todos los commits y sus padres
            cmd = ["git", "rev_list", "--all", "--parents"]
            result = subprocess.check_output(
                cmd,
                cwd=self.repo_path,
                text=True,
                stderr=subprocess.DEVNULL
            )

            self._parse_git_output(result)
            self._build_graph()
            self._calculate_levels()
            self.__analyze_commit_types()
        
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error al ejecutar git: {e}")
    
    def _parse_git_output(self, git_output: str) -> None:
        """Parsear la salida de git para extraer commits y sus padres."""
        for line in git_output.strip().split('\n'):
            if not line:
                continue

            parts = line.split()
            commit = parts[0]
            parents = parts[1:] if len(parts) > 1 else []

            self.commits[commit] = {
                'hash': commit,
                'parents': parents,
                'children': [],
                'type': 'root' if not parents else 'unknown'
            }       
    
    def _build_graph(self) -> None:
        """Costruir NetworkX DiGraph a partir de los commits."""
        # Agrega todos los commits como nodos
        for commit_hash in self.commits:
            self.graph.add_node(commit_hash)
        
        # Agrega aristas entre padres e hijos
        for commit_hash, commit_info in self.commits.items():
            for parent in commit_info['parents']:
                if parent in self.commits:
                    self.graph.add_edge(parent, commit_hash)
                    self.commits[parent]['children'].append(commit_hash)

    def _calculate_levels(self) -> None:
        """Calcular niveles de commits (distancia desde la raíz)."""
        # Buscar nodos raíz (sin padres)
        roots = [commit for commit, info in self.commits.items() 
                if not info['parents']]
        
        if not roots:
            return
        
        # BFS para calcular niveles
        queue = deque([(root, 0) for root in roots])
        visited = set()
        
        while queue:
            commit, level = queue.popleft()
            if commit in visited:
                continue
                
            visited.add(commit)
            self.levels[commit] = level
        
        # Añade hijos a la cola
        for child in self.commits[commit]['children']:
                if child not in visited:
                    queue.append((child, level + 1))

    def __analyze_commit_types(self) -> None:
        """Analizar tipos de commits y calcular métricas."""
        for commit_hash, commit_info in self.commits.items():
            parent_count = len(commit_info['parents'])
            
            if parent_count == 0:
                commit_info['type'] = 'root'
            elif parent_count == 1:
                commit_info['type'] = 'fast-forward'
            else:
                commit_info['type'] = 'merge'

    def calculate_branch_density(self) -> float:
        """
        Calcular la métrica de densidad de sucursales.
        Fórmula: numero de nodos(commits) / numero máximo de nodos en un nivel.
        """
        
        if not self.levels:
            return 0.0
        
        num_nodes = len(self.commits)
        max_level = max(self.levels.values()) if self.levels else 0
        
        if max_level == 0:
            density = float(num_nodes)
        else:
            density = num_nodes / (max_level + 1)  # +1 porque los niveles empiezan en 0
        
        self.metrics['branch_density'] = density
        return density
        
    
    def find_critical_merge_path(self, target_tag: str = "v0.0.0") -> List[str]:
        """
        Encuentre la ruta de fusión crítica utilizando la inversa de Dijkstra.
        Costo: 1 por merge, 0 por fast-forward.
        """
        try:
            # Obtener el commit HEAD
            head_result = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                text=True,
                stderr=subprocess.DEVNULL
            )
            head_commit = head_result.strip()
            
            # Obtener el target tag de un commit
            try:
                tag_result = subprocess.check_output(
                    ["git", "rev-parse", target_tag],
                    cwd=self.repo_path,
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                target_commit = tag_result.strip()
            except subprocess.CalledProcessError:
                # Si no se encuentra el tag, buscar el commit más antiguo
                target_commit = self._find_oldest_commit()
            
            path = self._dijkstra_merge_path(head_commit, target_commit)
            self.metrics['critical_merge_path'] = path
            return path
            
        except subprocess.CalledProcessError:
            # Fallback: retorna una lista vacía si falla
            self.metrics['critical_merge_path'] = []
            return []
        
    def _find_oldest_commit(self) -> str:
        """Busca el commit más antiguo en el repositorio."""
        if not self.levels:
            return list(self.commits.keys())[0] if self.commits else ""
        
        return min(self.levels, key=self.levels.get)
    
    def _dijkstra_merge_path(self, start: str, end: str) -> List[str]:
        """
        Modificación de Dijkstra para encontrar el costo minimo considerando costos de merges.
        """
        if start == end:
            return [start]
        
        if start not in self.commits or end not in self.commits:
            return []
        
        # Cola prioridad: (cost, commit, path)
        queue = [(0, start, [start])]
        visited = set()
        
        while queue:
            queue.sort()  # Implementación simple de cola de prioridad
            cost, current, path = queue.pop(0)
            
            if current in visited:
                continue
                
            visited.add(current)
            
            if current == end:
                return path
            
            # Explorar padres
            for parent in self.commits[current]['parents']:
                if parent not in visited:
                    # Calcular costo del edge
                    edge_cost = 1 if self.commits[current]['type'] == 'merge' else 0
                    new_cost = cost + edge_cost
                    new_path = path + [parent]
                    queue.append((new_cost, parent, new_path))
        
        return []  # Si no se encuentra un camino   
    
    def calculate_historical_entropy(self) -> float:
        """Calcular la métrica de entropía histórica."""
        
        event_counts = defaultdict(int)
        total_events = 0
        
        for commit_info in self.commits.values():
            if commit_info['type'] in ['merge', 'fast-forward']:
                event_counts[commit_info['type']] += 1
                total_events += 1
        
        if total_events == 0:
            self.metrics['historial_entropy'] = 0.0
            return 0.0
        
        # Calculando entropia
        entropy = 0.0
        for event_type, count in event_counts.items():
            probability = count / total_events
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        self.metrics['historial_entropy'] = entropy
        return entropy
    
    

    def export_metrics(self, output_path: str) -> None:
        """Exportar metricas en un archivo JSON."""
        self.calculate_branch_density()
        self.find_critical_merge_path()
        self.calculate_historical_entropy()

        self.metrics['metada'] = {
            'repository_path': str(self.repo_path),
            'analysis_version': '1.0.0',
            'total_metrics_calculated': len([k for k in self.metrics.keys() if k != 'metadata'])
        }

        with open(output_path, 'w') as f:
            json.dump(self.metrics, f, indent=2, sort_keys=True)

    def get_metrics(self) -> Dict[str, Any]:
        """Obtener las métricas calculadas."""
        return self.metrics.copy()
    
def main():
    """Función principal para ejecutar el análisis desde la línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Aanalizar el gráfico del repositorio de Git",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Ejemplo:
        python graph_analysis.py --repo . --output metrics.json
        python graph_analysis.py --repo /path/to/repo --output analysis.json --tag v1.0.0
        """
    )

    parser.add_argument(
        "--repo", 
        default=".", 
        help="Repositorio path (default: current directory)"
    )
    parser.add_argument(
        "--output", 
        default="metrics.json", 
        help="Ruta de salida del archivo JSON (default: metrics.json)"
    )
    parser.add_argument(
        "--tag",
        default="v0.0.0",
        help="Etiqueta de destino para el PATH (default: v0.0.0)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Habilitar salida detallada durante el análisis"
    )
    
    args = parser.parse_args()
    
    try:
        if args.verbose:
            print(f"Analizando repositorio: {args.repo}")
        
        analyzer = GitGraphAnalyzer(args.repo)
        analyzer.load_git_data()
        
        if args.verbose:
            print(f"Cargando {len(analyzer.commits)} commits")
            print("Calculando metricas.")
        
        # Calcular métricas con los tag
        analyzer.calculate_branch_density()
        analyzer.find_critical_merge_path(args.tag)
        analyzer.calculate_historical_entropy()
        analyzer.generate_summary_stats()
        
        # Resultados exportados
        analyzer.export_metrics(args.output)
        
        if args.verbose:
            metrics = analyzer.get_metrics()
            print(f"\nResultados:")
            print(f"  Densidad de rama: {metrics.get('branch_density', 0):.3f}")
            print(f"  Historial Entropía: {metrics.get('historical_entropy', 0):.3f}")
            print(f"  Longitug del PATH: {len(metrics.get('critical_merge_path', []))}")
            print(f"  Total Commits: {metrics.get('total_commits', 0)}")
        
        print(f"Analis completo. Metricas guardado en {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())