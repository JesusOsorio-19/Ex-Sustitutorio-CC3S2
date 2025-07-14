import pytest
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.graph_anaylisis import GitGraphAnalyzer

class TestGitGraphAnalyzer:
    """Casos de tests para GitGraphAnalyzer."""

    @pytest.fixture
    def temp_repo(self):
        """Crear un repositorio git temporal para pruebas."""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)

        # Configurar un repositorio git mínimo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, 
                      capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], 
                      cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], 
                      cwd=repo_path, check=True)
        
        # Crear un commit inicial
        test_file = repo_path / "test.txt"
        test_file.write_text("Contenido inicial")
        subprocess.run(["git", "add", "test.txt"], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Commit inicial"], 
                      cwd=repo_path, check=True)
        
        yield repo_path
        
        # Limpiar
        shutil.rmtree(temp_dir)
        
    def test_initialization(self):
        """Test de inicialización del analizador."""
        analyzer = GitGraphAnalyzer(".")
        assert analyzer.repo_path == Path(".")
        assert analyzer.graph is not None
        assert analyzer.metrics == {}

    def test_load_git_data_real_repo(self, temp_repo):
        """Test de carga de datos git desde un repositorio real."""
        analyzer = GitGraphAnalyzer(str(temp_repo))
        analyzer.load_git_data()
        
        assert len(analyzer.commits) >= 1
        assert analyzer.graph.number_of_nodes() >= 1
    
    @patch('subprocess.check_output')
    def test_parse_git_output(self, mock_subprocess):
        """Test de análisis de salida de git rev-list."""
        mock_output = """abc123 def456
        def456
        ghi789 def456 jkl012
        """
                
        mock_subprocess.return_value = mock_output
        
        analyzer = GitGraphAnalyzer(".")
        analyzer.load_git_data()
        
        # Verificar que los commits se parsearon correctamente
        assert len(analyzer.commits) == 3
        assert 'abc123' in analyzer.commits
        assert analyzer.commits['abc123']['parents'] == ['def456']
        assert analyzer.commits['def456']['parents'] == []
        assert analyzer.commits['ghi789']['parents'] == ['def456', 'jkl012']
    
    def test_calculate_branch_density(self):
        """Test de cálculo de densidad de ramas."""
        analyzer = GitGraphAnalyzer(".")
        
        # Configurar datos de prueba
        analyzer.commits = {
            'commit1': {'parents': [], 'children': ['commit2'], 'type': 'root'},
            'commit2': {'parents': ['commit1'], 'children': ['commit3'], 'type': 'fast-forward'},
            'commit3': {'parents': ['commit2'], 'children': [], 'type': 'fast-forward'}
        }
        analyzer.levels = {'commit1': 0, 'commit2': 1, 'commit3': 2}
        
        density = analyzer.calculate_branch_density()
        expected = 3 / 3  # 3 nodos, max nivel 2 (hasta 3 niveles en total)
        assert density == expected
    
    def test_calculate_historical_entropy(self):
        """Test historical entropy calculation."""
        analyzer = GitGraphAnalyzer(".")
        
        # Configurar datos de prueba: 2 merges, 1 fast-forward
        analyzer.commits = {
            'commit1': {'type': 'root'},
            'commit2': {'type': 'fast-forward'},
            'commit3': {'type': 'merge'},
            'commit4': {'type': 'merge'}
        }
        
        entropy = analyzer.calculate_historical_entropy()
        
        # Expected: p(merge) = 2/3, p(fast-forward) = 1/3
        # H = -(2/3 * log2(2/3) + 1/3 * log2(1/3))
        import math
        expected = -(2/3 * math.log2(2/3) + 1/3 * math.log2(1/3))
        assert abs(entropy - expected) < 0.001

    def test_calculate_historical_entropy(self):
        """Test cálculo de entropía histórica."""
        analyzer = GitGraphAnalyzer(".")
        
        # Configurar datos de prueba: 2 merges, 1 fast-forward
        analyzer.commits = {
            'commit1': {'type': 'root'},
            'commit2': {'type': 'fast-forward'},
            'commit3': {'type': 'merge'},
            'commit4': {'type': 'merge'}
        }
        
        entropy = analyzer.calculate_historical_entropy()
        
        # Expected: p(merge) = 2/3, p(fast-forward) = 1/3
        # H = -(2/3 * log2(2/3) + 1/3 * log2(1/3))
        import math
        expected = -(2/3 * math.log2(2/3) + 1/3 * math.log2(1/3))
        assert abs(entropy - expected) < 0.001
    
    def test_find_critical_merge_path_simple(self):
        """Test critical merge path finding."""
        analyzer = GitGraphAnalyzer(".")
        
        # Configurar historia lineal simple
        analyzer.commits = {
            'head': {'parents': ['middle'], 'children': [], 'type': 'fast-forward'},
            'middle': {'parents': ['old'], 'children': ['head'], 'type': 'merge'},
            'old': {'parents': [], 'children': ['middle'], 'type': 'root'}
        }
        analyzer._build_graph()
        
        with patch('subprocess.check_output') as mock_subprocess:
            mock_subprocess.side_effect = ['head', 'old']
            path = analyzer.find_critical_merge_path()
            
            assert 'head' in path
            assert 'old' in path

    def test_export_metrics(self, temp_repo):
        """Test métrica de exportación a JSON."""
        analyzer = GitGraphAnalyzer(str(temp_repo))
        analyzer.load_git_data()
        
        output_file = temp_repo / "test_metrics.json"
        analyzer.export_metrics(str(output_file))
        
        # Verificar que el archivo se creó
        assert output_file.exists()
        
        with open(output_file) as f:
            metrics = json.load(f)
        
        # Verificar que las métricas contienen los campos esperados
        assert 'branch_density' in metrics
        assert 'historical_entropy' in metrics
        assert 'total_commits' in metrics
        assert 'metadata' in metrics

    def test_levels_calculation(self):
        """Test commit level calculation."""
        analyzer = GitGraphAnalyzer(".")
        
        # Cofigurar estructura ramificada
        # Estructura: root -> a, b; a -> merge; b -> merge
        analyzer.commits = {
            'root': {'parents': [], 'children': ['a', 'b']},
            'a': {'parents': ['root'], 'children': ['merge']},
            'b': {'parents': ['root'], 'children': ['merge']},
            'merge': {'parents': ['a', 'b'], 'children': []}
        }
        analyzer._build_graph()
        analyzer._calculate_levels()
        
        assert analyzer.levels['root'] == 0
        assert analyzer.levels['a'] == 1
        assert analyzer.levels['b'] == 1
        assert analyzer.levels['merge'] == 2
