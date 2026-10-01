from pathlib import Path
import datetime as dt
import pytest
from src.excel_loader import load_excel_files
from src.ft_model import build_ft_table, proto_summary, SIT_BOTH, SIT_STUDY, SIT_FAB, SIT_OK

TODAY = dt.date(2026, 10, 1)


def test_real_workbooks_smoke():
    """Avec les vrais .xlsm copiés dans data/ : chaque prototype doit produire des FT, et P1 doit contenir sa partie Étude ET Fabrication."""
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / "data").glob("*.xlsm"))
    if not paths:
        pytest.skip("Aucun .xlsm dans data/ : copier les vrais classeurs pour ce test.")
    sheets, errors = load_excel_files([{"name": p.name, "content": p.read_bytes()} for p in paths])
    assert sheets, errors
    ft = build_ft_table(sheets, TODAY)
    assert not ft.empty
    p1 = ft[ft["prototype"].eq("P1")]
    assert len(p1) > 100
    assert p1["etude_statut"].ne("NON RENSEIGNE").any(), "Aucun statut étude lu pour P1"
    assert p1["fab_statut"].ne("NON RENSEIGNE").any(), "Aucun statut fabrication lu pour P1"
    assert not proto_summary(ft).empty
