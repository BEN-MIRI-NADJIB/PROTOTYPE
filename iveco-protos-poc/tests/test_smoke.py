from pathlib import Path
from src.excel_loader import load_excel_files
from src.concatenation import concatenate_sheets, split_business_tables
from src.cleaning import clean_dataframe
from src.impacts import build_impact_table


def test_real_workbooks_smoke():
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / "data").glob("*.xlsm"))
    if not paths: return
    payloads = [{"name": p.name, "content": p.read_bytes()} for p in paths]
    sheets, errors = load_excel_files(payloads)
    assert sheets, errors
    data = clean_dataframe(concatenate_sheets(sheets))
    assert not data.empty
    assert {"phase", "fichier_source", "feuille_source", "cle_metier"}.issubset(data.columns)
    tables = split_business_tables(data)
    assert "etude" in tables and "fabrication" in tables
    impacts = build_impact_table(data)
    assert impacts is not None
