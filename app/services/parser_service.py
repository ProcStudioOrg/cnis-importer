"""Wraps CNISParserFinal with proper temp file handling."""

import os
import sys
import tempfile
import logging

import pdfplumber

# Add project root to path so we can import the parser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from cnis_parser_final import CNISParserFinal

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Raised when the parser fails to extract data."""
    pass


class UnsupportedCNISError(ParseError):
    """Raised when the CNIS variant is recognized but not yet supported."""
    pass


def _check_cnis_variant(pdf_path: str) -> None:
    """Reject the simplified 'Relações Previdenciárias' variant.

    Complete CNIS reports contain 'Extrato Previdenciário' on page 1; the
    simplified variant replaces that title with 'Relações Previdenciárias'
    and ships no remuneration data, which the parser cannot yet handle.
    """
    with pdfplumber.open(pdf_path) as pdf:
        first_page_text = pdf.pages[0].extract_text() or ""

    if "Extrato Previdenciário" in first_page_text:
        return

    is_cnis = "Cadastro Nacional de Informações Sociais" in first_page_text
    if is_cnis and "Relações Previdenciárias" in first_page_text:
        raise UnsupportedCNISError(
            "Extrato previdenciário simplificado não suportado ainda - "
            "faça o download da versão completa"
        )


def parse_pdf(file_bytes: bytes) -> dict:
    """Parse a CNIS PDF from bytes. Returns the raw parser dict."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        _check_cnis_variant(tmp_path)

        parser = CNISParserFinal(pdf_path=tmp_path, debug=False)
        result = parser.parse()

        if not result or not result.get('personal_info'):
            raise ParseError("Could not extract data from PDF")

        return result

    except ParseError:
        raise
    except Exception as e:
        logger.exception("Parser failed")
        raise ParseError(f"Failed to parse CNIS PDF: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
