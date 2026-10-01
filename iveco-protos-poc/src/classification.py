import re
import unicodedata
import pandas as pd

STUDY_SHEETS = ("ft_impact", "cid", "dap", "next_3w", "kpi_system", "target_by_file")
MANUFACTURING_SHEETS = ("ebom", "build", "steps", "supplier", "cluster_demo", "follow_up", "all_not_for_demo")
PLANNING_SHEETS = ("pq", "pt", "plan", "progress", "completion", "r01_concac")
COST_WORDS = ("cost", "cout", "price", "prix", "budget", "montant")

STUDY_WORDS = {
    "ft", "dmu", "cid", "dap", "maturity", "maturite", "criticity", "criticite",
    "systems", "systeme", "subsystems", "proto_impact", "impact_global", "design"
}
MANUFACTURING_WORDS = {
    "part_number", "supplier", "fournisseur", "order", "commande", "material", "matiere",
    "receival", "reception", "ebom", "quantity", "quantite", "build", "assembly", "assemblage",
    "prototype_request", "pr_status", "rda", "retrofit", "plan_b"
}


def norm(value) -> str:
    if value is None or pd.isna(value):
        value = ""
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii").lower().strip()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def classify_sheet(sheet_name: str, dataframe: pd.DataFrame) -> str:
    name = norm(sheet_name)
    cols = {norm(c) for c in dataframe.columns}
    if any(k in name for k in COST_WORDS) or any(any(k in c for k in COST_WORDS) for c in cols):
        if not any(k in name for k in STUDY_SHEETS + MANUFACTURING_SHEETS):
            return "COUT"
    if any(k in name for k in MANUFACTURING_SHEETS):
        return "FABRICATION"
    if any(k in name for k in STUDY_SHEETS):
        return "ETUDE"
    if any(k in name for k in PLANNING_SHEETS):
        return "PLANNING"
    study_score = len(cols & STUDY_WORDS)
    manufacturing_score = len(cols & MANUFACTURING_WORDS)
    if manufacturing_score > study_score and manufacturing_score >= 2:
        return "FABRICATION"
    if study_score >= 2:
        return "ETUDE"
    return "AUTRE"


def normalize_status(value) -> str:
    text = norm(value)
    if not text:
        return "NON RENSEIGNE"
    if text in {"0", "x"}: return "NON RENSEIGNE"
    if any(k in text for k in ("cancel", "annul")): return "ANNULE"
    if text in {"in_line", "on_time", "no_check_needed", "not_needed"}: return "OK"
    if text.startswith("email_sent") or text in {"open", "opened", "waiting_dmu_check"}: return "EN COURS"
    if any(k in text for k in ("borderline", "at_risk", "risk")): return "A RISQUE"
    if any(k in text for k in ("late", "retard", "delayed")): return "EN RETARD"
    if any(k in text for k in ("missing", "not_found", "not_exist")): return "MANQUANT"
    if text in {"ko", "nok"} or text.startswith("ko_"): return "KO"
    if any(k in text for k in ("progress", "ongoing", "in_work")): return "EN COURS"
    if any(k in text for k in ("closed", "complete", "completed", "approved", "sent", "done")): return "TERMINE"
    if text == "ok" or text.startswith("ok_"): return "OK"
    if any(k in text for k in ("to_do", "planned", "planifie")): return "A FAIRE"
    return str(value).strip().upper()
