import pandas as pd

META = {"id_ligne", "fichier_source", "feuille_source", "ligne_source", "cle_metier"}


def validate_dataframe(dataframe: pd.DataFrame) -> dict:
    if dataframe.empty:
        return {"total_rows": 0, "duplicate_rows": 0, "missing_cells": 0, "negative_values": 0, "quality_score": 100., "issues": pd.DataFrame()}
    issues = []
    cols = [c for c in dataframe.columns if c not in META]
    duplicated = dataframe.duplicated(subset=[c for c in ("fichier_source", "feuille_source", "ligne_source") if c in dataframe.columns], keep=False)
    for _, r in dataframe[duplicated].iterrows():
        issues.append({"id_ligne": r.get("id_ligne"), "severite": "Moyenne", "type_anomalie": "Doublon source", "message": "Même ligne source chargée plusieurs fois."})
    rules = [
        ("ETUDE", "ft", "FT manquante dans une donnée d'étude", "Haute"),
        ("FABRICATION", "ft", "FT manquante dans une donnée de fabrication", "Haute"),
        ("FABRICATION", "prototype", "Prototype non identifié", "Haute"),
    ]
    for phase, col, msg, sev in rules:
        if "phase" in dataframe.columns and col in dataframe.columns:
            mask = dataframe["phase"].eq(phase) & dataframe[col].isna()
            for _, r in dataframe[mask].head(2000).iterrows():
                issues.append({"id_ligne": r.get("id_ligne"), "severite": sev, "type_anomalie": "Champ métier manquant", "message": msg})
    missing = int(dataframe[cols].isna().sum().sum()) if cols else 0
    numeric = dataframe[cols].select_dtypes(include="number") if cols else pd.DataFrame()
    negatives = int(numeric.lt(0).sum().sum()) if not numeric.empty else 0
    total_cells = max(len(dataframe) * max(len(cols), 1), 1)
    score = max(0., 100. - (missing/total_cells)*25 - (duplicated.sum()/max(len(dataframe),1))*35)
    return {"total_rows": len(dataframe), "duplicate_rows": int(duplicated.sum()), "missing_cells": missing, "negative_values": negatives, "quality_score": score, "issues": pd.DataFrame(issues)}
