import re
import numpy as np
import pandas as pd

EMPTY = {"", "-", "--", "n/a", "na", "nan", "none", "null", "(vide)", "<na>"}
META = {"id_ligne", "ligne_source", "fichier_source", "feuille_source", "phase", "cle_metier"}


def _clean(value):
    if not isinstance(value, str): return value
    value = re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()
    return pd.NA if value.lower() in EMPTY else value


def clean_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty: return dataframe.copy()
    result = dataframe.copy()
    for col in result.select_dtypes(include=["object", "string"]).columns:
        result[col] = result[col].map(_clean)
    for col in result.columns:
        if col in META or pd.api.types.is_numeric_dtype(result[col]): continue
        prepared = (result[col].astype("string").str.replace("\u00a0", "", regex=False)
                    .str.replace("k€", "", regex=False).str.replace("€", "", regex=False)
                    .str.replace(" ", "", regex=False).str.replace(",", ".", regex=False))
        numeric = pd.to_numeric(prepared, errors="coerce")
        count = int(result[col].notna().sum())
        if count and numeric.notna().sum() / count >= .85:
            result[col] = numeric
    result = result.replace([np.inf, -np.inf], np.nan).dropna(axis=0, how="all").reset_index(drop=True)
    if "id_ligne" not in result.columns:
        result.insert(0, "id_ligne", np.arange(1, len(result)+1))
    return result
