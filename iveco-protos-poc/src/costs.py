import re
import pandas as pd

COST_PATTERNS = ("cout", "cost", "prix", "price", "budget", "montant")
EXCLUDED = ("quantity", "quantite", "week", "semaine", "year", "annee", "id", "volume", "plan", "sent", "nb_")


def _numeric(value):
    if pd.isna(value): return None
    if isinstance(value, (int, float)): return float(value)
    text = str(value).lower().replace("\u00a0", "").replace("k€", "").replace("keur", "").replace("€", "").replace(" ", "").replace(",", ".")
    return float(text) if re.fullmatch(r"-?\d+(?:\.\d+)?", text) else None


def extract_costs(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty: return pd.DataFrame()
    columns = [c for c in dataframe.columns if any(p in c.lower() for p in COST_PATTERNS) and not any(x in c.lower() for x in EXCLUDED)]
    records = []
    for row in dataframe.itertuples(index=False):
        d = row._asdict()
        for col in columns:
            value = _numeric(d.get(col))
            if value is None: continue
            records.append({
                "id_ligne": d.get("id_ligne"), "cle_metier": d.get("cle_metier"), "prototype": d.get("prototype"),
                "ft": d.get("ft"), "departement": d.get("departement"), "phase": d.get("phase"),
                "fichier_source": d.get("fichier_source"), "feuille_source": d.get("feuille_source"),
                "variable_cout": col, "cout_detecte": value,
            })
    return pd.DataFrame(records)


def calculate_cost_kpis(costs: pd.DataFrame) -> dict:
    values = pd.to_numeric(costs.get("cout_detecte", pd.Series(dtype=float)), errors="coerce").dropna()
    if values.empty: return {"total_cost": 0., "average_cost": 0., "median_cost": 0., "maximum_cost": 0., "minimum_cost": 0., "cost_count": 0}
    return {"total_cost": float(values.sum()), "average_cost": float(values.mean()), "median_cost": float(values.median()), "maximum_cost": float(values.max()), "minimum_cost": float(values.min()), "cost_count": int(values.count())}
