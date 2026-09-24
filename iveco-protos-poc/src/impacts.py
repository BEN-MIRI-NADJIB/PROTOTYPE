import re
import pandas as pd
from src.classification import normalize_status

RISK_POINTS = {"KO": 30, "EN RETARD": 25, "MANQUANT": 22, "A RISQUE": 18, "EN COURS": 8, "NON RENSEIGNE": 10}
CRITICAL_STEPS = ("structure", "body assembly", "mecanical", "mechanical", "electrical wiring", "dashboard", "roof building")


def _first(row, names, default=pd.NA):
    for name in names:
        value = row.get(name)
        if value is not None and not pd.isna(value) and str(value).strip(): return value
    return default


def _status(row):
    raw = _first(row, ["statut_impact", "delta_forecast_vs_need", "statut_ft", "statut_dmu", "status"])
    return normalize_status(raw)


def _risk_label(score):
    if score >= 61: return "CRITIQUE"
    if score >= 41: return "ELEVE"
    if score >= 21: return "MODERE"
    return "FAIBLE"


def _consequence(status, step, plan_b, phase):
    step_text = "" if step is None or pd.isna(step) else str(step).lower()
    pb = "" if plan_b is None or pd.isna(plan_b) else str(plan_b).lower()
    if status in {"KO", "MANQUANT", "EN RETARD", "A RISQUE"}:
        if phase == "ETUDE":
            base = "Validation technique susceptible de bloquer le lancement de l'approvisionnement."
        else:
            base = "Réception ou disponibilité susceptible de retarder le montage."
        if any(k in step_text for k in CRITICAL_STEPS): base += " Étape de fabrication critique exposée."
        if "valid" in pb: base += " Plan B identifié, avec retrofit possible."
        elif not pb or pb in {"nan", "<na>", "none"}: base += " Aucun Plan B renseigné."
        return base
    return "Aucune conséquence bloquante détectée avec les informations disponibles."


def build_impact_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty: return pd.DataFrame()
    rows = []
    for _, r in dataframe.iterrows():
        row = r.to_dict(); phase = str(row.get("phase", "AUTRE"))
        if phase not in {"ETUDE", "FABRICATION"}: continue
        status = _status(row)
        step = _first(row, ["etape_fabrication", "step", "build_steps"])
        plan_b = _first(row, ["plan_b", "demo_plan_b_status", "plan_b_detail"])
        score = RISK_POINTS.get(status, 0)
        if any(k in str(step).lower() for k in CRITICAL_STEPS): score += 15
        if pd.isna(plan_b) or not str(plan_b).strip(): score += 10
        if pd.isna(_first(row, ["responsable", "owner", "ft_responsible"])): score += 5
        score = min(score, 100)
        if score == 0 and status in {"OK", "TERMINE"}: continue
        rows.append({
            "id_ligne": row.get("id_ligne"), "cle_metier": row.get("cle_metier"), "prototype": row.get("prototype"),
            "ft": row.get("ft"), "description": _first(row, ["description", "description_fr"]),
            "departement": row.get("departement"), "phase_origine": phase, "statut": status,
            "etape_impactee": step, "plan_b": plan_b, "responsable": _first(row, ["responsable", "owner", "ft_responsible"]),
            "date_besoin_piece": row.get("date_besoin_piece"), "date_dap_prevue": row.get("date_dap_prevue"),
            "date_dap_reelle": row.get("date_dap_reelle"), "score_risque": score, "niveau_risque": _risk_label(score),
            "consequence": _consequence(status, step, plan_b, phase),
            "action_recommandee": "Traiter la cause, confirmer le responsable et sécuriser un Plan B." if score >= 41 else "Surveiller et mettre à jour les dates et statuts.",
            "fichier_source": row.get("fichier_source"), "feuille_source": row.get("feuille_source"),
        })
    return pd.DataFrame(rows).sort_values("score_risque", ascending=False, ignore_index=True) if rows else pd.DataFrame()
