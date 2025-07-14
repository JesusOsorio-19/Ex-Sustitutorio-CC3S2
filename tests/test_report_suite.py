import pytest
from src.report_suite import ReportingSuite, MarkdownWriter

class TestReportingSuite:
    """Casos de testeo para ReportingSuite."""

    def test_initialization(self):
        """Test de inicialización del ReportingSuite."""
        writer = MarkdownWriter()
        suite = ReportingSuite(writer)
        assert suite.writer is writer