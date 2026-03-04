import pytest
import sys
import os

# Adiciona o diretório raiz ao path para importar pacotes root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autofill_conversao import find_best_attribute_match

@pytest.fixture
def mock_pg_attrs():
    """Mock do PostGIS target fields para servir the candidatos do fuzzy."""
    return [
        {"nome": "tipoedifpubcivil"},
        {"nome": "tipousoedif"},
        {"nome": "nome"},
        {"nome": "geometriaaproximada"},
        {"nome": "situacaofisica"}
    ]

def test_exact_attribute_match(mock_pg_attrs):
    """Testa se uma string exata ganha match limpo usando Lowercase."""
    result = find_best_attribute_match("NOME", mock_pg_attrs)
    assert result == "nome"

def test_fuzzy_attribute_match(mock_pg_attrs):
    """Testa o motor difflib retornando a string mais próxima."""
    # "situafisic" is cut off, so it should fuzzy match "situacaofisica"
    # Although 'situafisic' is in overrides, let's test a fake one that uses fuzzy
    # To test pure fuzzy:
    fake_pg = [{"nome": "operacional"}]
    result = find_best_attribute_match("operacion", fake_pg)
    assert result == "operacional"

def test_manual_override_precedence(mock_pg_attrs):
    """Testa se o Override manual sobrevive ao invés do Fuzzy Motor (Caso TIPOEDIF Guarda Municipal)."""
    # A string Shape 'TIPOEDIF' deveria bater em 'tipousoedif' devido ao override,
    # mesmo que pudesse ficar confusa com 'tipoedifpubcivil'
    result = find_best_attribute_match("TIPOEDIF", mock_pg_attrs)
    assert result == "tipousoedif"
    
def test_no_match(mock_pg_attrs):
    """Se nenhum target se aproximar da similaridade mínima (0.6) deve retornar nulo."""
    result = find_best_attribute_match("ID_ESTRANHO_XXZY", mock_pg_attrs)
    assert result is None
