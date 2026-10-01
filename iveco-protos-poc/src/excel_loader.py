from io import BytesIO
from pathlib import Path
import re
import unicodedata
import warnings
import pandas as pd
from src.classification import classify_sheet, norm, normalize_status

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Feuilles réellement utiles : FT par prototype, fournisseurs, CID, planning MASTER.
# Les autres (KPI, macros, historiques, 'Mistake Tracer' d'un million de lignes...) ralentissent sans rien apporter.
BUSINESS_SHEETS = {"ft_impact", "ft_impact_global", "cid_stato_n", "r01_concac_proto", "ft_steps"}


def is_business_sheet(sheet_name: str) -> bool:
    name = norm(sheet_name)
    return name in BUSINESS_SHEETS or name.startswith("supplier_list")

HEADER_KEYWORDS = {
    "ft", "description_english", "description_french", "dpt_ng", "proto_impact", "cid", "dap",
    "part_number", "year", "week", "plan", "sent", "supplier", "material", "build_steps",
    "systems", "systems_domain", "proto_id", "category", "unit"
}
ALIASES = {
    "dpt": "departement", "dpt_ng": "departement", "dept": "departement", "department": "departement",
    "proto_id": "prototype", "prototype_id": "prototype", "support": "prototype",
    "description_english": "description", "description_french": "description_fr",
    "systems_domain": "domaine_systeme", "systems": "systeme", "subsystems": "sous_systeme",
    "dap_number": "dap", "change_cid": "cid", "part_nr": "part_number", "part_no": "part_number",
    "material_receival_date_forecast": "date_reception_prevue", "date_parts_needed_by_proto": "date_besoin_piece",
    "dap_submission_forecast": "date_dap_prevue", "dap_submitted_date": "date_dap_reelle",
    "new_build_step_pe": "etape_fabrication", "build_steps": "etape_fabrication",
    "delta_forecast_vs_need": "statut_impact", "impact_of_delay_if_late": "consequence",
    "demo_plan_b_status": "plan_b", "plan_b_demo": "plan_b_detail", "owner": "responsable",
    "ft_status": "statut_ft", "check_dmu_status": "statut_dmu", "maturity_at_part_order": "maturite",
    "material_cost": "cout_reel", "material_cost_eur": "cout_reel", "montant_k": "cout_reel_keur",
}


def _ascii(value) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return text.encode("ascii", "ignore").decode("ascii")


def _unique(columns):
    out, counts = [], {}
    for i, col in enumerate(columns):
        base = (norm(col) or f"variable_{i+1}")[:60]
        base = ALIASES.get(base, base)
        counts[base] = counts.get(base, 0) + 1
        out.append(base if counts[base] == 1 else f"{base}_{counts[base]}")
    return out


def _prepare(payload):
    if isinstance(payload, dict):
        name = payload.get("name") or payload.get("filename") or "fichier.xlsx"
        content = payload.get("content") or payload.get("data")
    else:
        name = getattr(payload, "name", "fichier.xlsx")
        content = payload.getvalue() if hasattr(payload, "getvalue") else payload.read()
    if not isinstance(content, (bytes, bytearray)):
        raise ValueError("Contenu Excel invalide")
    return Path(str(name)).name, BytesIO(bytes(content))


def _header_row(raw: pd.DataFrame) -> int:
    best_idx, best_score = 0, -1
    for idx in range(min(len(raw), 80)):
        vals = [norm(v) for v in raw.iloc[idx].tolist() if pd.notna(v)]
        exact_hits = sum(1 for v in vals if v in HEADER_KEYWORDS)
        partial_hits = sum(1 for v in vals if v not in HEADER_KEYWORDS and any(len(k) > 3 and k in v for k in HEADER_KEYWORDS))
        unique_text = len({v for v in vals if v})
        score = exact_hits * 15 + partial_hits * 3 + min(unique_text, 20)
        if score > best_score:
            best_idx, best_score = idx, score
    return best_idx


def _parse_week(value):
    text = str(value or "").strip().upper()
    match = re.search(r"(?:20)?(\d{2})\s*W\s*(\d{1,2})", text)
    if match:
        return int("20" + match.group(1)), int(match.group(2))
    return pd.NA, pd.NA


def _derive_prototype(file_name: str, frame: pd.DataFrame):
    match = re.search(r"(?:follow[-_ ]?up[-_ ]?)?(P\d+)", file_name, re.I)
    fallback = match.group(1).upper() if match else pd.NA
    if "prototype" not in frame.columns:
        frame["prototype"] = fallback
    else:
        frame["prototype"] = frame["prototype"].fillna(fallback)
    return frame


def _standardize(frame: pd.DataFrame, file_name: str, sheet_name: str, header_row: int) -> pd.DataFrame:
    frame = frame.dropna(axis=0, how="all").dropna(axis=1, how="all").copy()
    frame.columns = _unique(frame.columns)
    frame = _derive_prototype(file_name, frame)
    frame.insert(0, "ligne_source", frame.index + header_row + 2)
    frame.insert(0, "feuille_source", sheet_name)
    frame.insert(0, "fichier_source", file_name)
    phase = classify_sheet(sheet_name, frame)
    frame.insert(3, "phase", phase)
    if "prototype" in frame.columns:
        frame["prototype"] = frame["prototype"].astype("string").str.strip().replace({"": pd.NA})
    for candidate in ("statut_ft", "statut_dmu", "statut_impact", "status", "statut"):
        if candidate in frame.columns:
            frame[f"{candidate}_normalise"] = frame[candidate].map(normalize_status)
    # Dates ISO semaine vers année/semaine auxiliaires
    for source in ("date_dap_prevue", "date_dap_reelle", "scheduled_date", "sending_date"):
        if source in frame.columns:
            parsed = frame[source].map(_parse_week)
            frame[f"{source}_annee"] = parsed.map(lambda x: x[0])
            frame[f"{source}_semaine"] = parsed.map(lambda x: x[1])
    key_parts = []
    for col in ("prototype", "ft", "departement"):
        if col in frame.columns:
            key_parts.append(frame[col].astype("string").fillna("").str.strip())
        else:
            key_parts.append(pd.Series([""] * len(frame), index=frame.index, dtype="string"))
    frame["cle_metier"] = key_parts[0] + "|" + key_parts[1] + "|" + key_parts[2]
    return frame.reset_index(drop=True)


def load_excel_file(payload, only_business=True):
    sheets, errors = [], []
    try:
        file_name, source = _prepare(payload)
        workbook = pd.ExcelFile(source, engine="openpyxl")
        for sheet_name in workbook.sheet_names:
            if only_business and not is_business_sheet(sheet_name):
                continue
            try:
                raw = pd.read_excel(workbook, sheet_name=sheet_name, header=None, dtype=object)
                raw = raw.dropna(axis=0, how="all").dropna(axis=1, how="all")
                if raw.empty:
                    continue
                h = _header_row(raw)
                header = _unique(raw.iloc[h].tolist())
                data = raw.iloc[h+1:].copy()
                data.columns = header
                data = _standardize(data, file_name, sheet_name, h)
                if not data.empty:
                    sheets.append({"file_name": file_name, "sheet_name": sheet_name, "phase": data["phase"].iloc[0], "dataframe": data})
            except Exception as exc:
                errors.append(f"{file_name} / {sheet_name}: {type(exc).__name__}")
        workbook.close()
    except Exception as exc:
        errors.append(f"{getattr(payload, 'name', 'fichier')}: impossible à ouvrir ({type(exc).__name__}).")
    return sheets, errors


def load_excel_files(payloads):
    all_sheets, all_errors = [], []
    for payload in payloads or []:
        sheets, errors = load_excel_file(payload)
        all_sheets.extend(sheets); all_errors.extend(errors)
    return all_sheets, all_errors
