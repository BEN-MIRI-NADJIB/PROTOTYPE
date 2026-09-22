import re
import unicodedata

import pandas as pd


COST_KEYWORDS = (
    "cost",
    "cout",
    "budget",
    "price",
    "prix",
    "amount",
    "montant",
    "total",
)


def normalize_value(value) -> str:
    if pd.isna(value):
        return ""

    normalized_value = unicodedata.normalize("NFKD", str(value))
    return normalized_value.encode("ascii", "ignore").decode("ascii").lower().strip()


def contains_cost_keyword(value) -> bool:
    normalized_value = normalize_value(value)
    return any(keyword in normalized_value for keyword in COST_KEYWORDS)


def extract_number(value):
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text_value = str(value).strip()
    text_value = (
        text_value.replace("\u00a0", "")
        .replace("k€", "")
        .replace("€", "")
        .replace("ke", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    if not re.fullmatch(r"-?\d+(?:\.\d+)?", text_value):
        return None

    try:
        return float(text_value)
    except ValueError:
        return None


def readable_label(row_dictionary: dict) -> str:
    label_parts = []

    for column in ("systeme", "projet", "composant", "prototype", "id_prototype", "designation"):
        value = row_dictionary.get(column)
        if value is not None and not pd.isna(value):
            label_parts.append(str(value))

    return " | ".join(label_parts) or "Cout detecte"


def extract_structured_costs(dataframe: pd.DataFrame) -> pd.DataFrame:
    cost_column = None

    for candidate in ("cout_ke", "cout", "cost", "budget", "total"):
        if candidate in dataframe.columns:
            cost_column = candidate
            break

    if cost_column is None:
        return pd.DataFrame()

    records = []

    for row in dataframe.itertuples(index=False):
        row_dictionary = row._asdict()
        numeric_value = extract_number(row_dictionary.get(cost_column))

        if numeric_value is None:
            continue

        records.append(
            {
                "id_ligne": row_dictionary.get("id_ligne"),
                "fichier_source": row_dictionary.get("fichier_source"),
                "feuille_source": row_dictionary.get("feuille_source"),
                "ligne_source": row_dictionary.get("ligne_source"),
                "systeme": row_dictionary.get("systeme"),
                "composant": row_dictionary.get("composant"),
                "prototype": row_dictionary.get("prototype"),
                "quantite": row_dictionary.get("quantite"),
                "prix_piece_ke": row_dictionary.get("prix_piece_ke"),
                "libelle_cout": readable_label(row_dictionary),
                "variable_cout": cost_column,
                "cout_detecte": numeric_value,
            }
        )

    return pd.DataFrame(records)


def extract_generic_costs(dataframe: pd.DataFrame) -> pd.DataFrame:
    metadata_columns = [
        column
        for column in ["id_ligne", "fichier_source", "feuille_source", "ligne_source"]
        if column in dataframe.columns
    ]

    data_columns = [column for column in dataframe.columns if column not in metadata_columns]
    numeric_columns = dataframe[data_columns].select_dtypes(include="number").columns.tolist()
    cost_named_columns = [column for column in numeric_columns if contains_cost_keyword(column)]

    if not cost_named_columns:
        cost_named_columns = numeric_columns

    extracted_costs = []

    for row in dataframe.itertuples(index=False):
        row_dictionary = row._asdict()
        row_labels = [
            str(row_dictionary.get(column))
            for column in data_columns
            if not pd.isna(row_dictionary.get(column))
            and contains_cost_keyword(row_dictionary.get(column))
        ]

        for column in cost_named_columns:
            numeric_value = extract_number(row_dictionary.get(column))

            if numeric_value is None:
                continue

            extracted_costs.append(
                {
                    "id_ligne": row_dictionary.get("id_ligne"),
                    "fichier_source": row_dictionary.get("fichier_source"),
                    "feuille_source": row_dictionary.get("feuille_source"),
                    "ligne_source": row_dictionary.get("ligne_source"),
                    "systeme": row_dictionary.get("systeme"),
                    "composant": row_dictionary.get("composant"),
                    "prototype": row_dictionary.get("prototype"),
                    "quantite": row_dictionary.get("quantite"),
                    "prix_piece_ke": row_dictionary.get("prix_piece_ke"),
                    "libelle_cout": " | ".join(row_labels[:3]) or column,
                    "variable_cout": column,
                    "cout_detecte": numeric_value,
                }
            )

    return pd.DataFrame(extracted_costs)


def extract_costs(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame()

    structured_costs = extract_structured_costs(dataframe)
    if not structured_costs.empty:
        return structured_costs

    return extract_generic_costs(dataframe)


def calculate_cost_kpis(costs_dataframe: pd.DataFrame) -> dict:
    empty_result = {
        "total_cost": 0.0,
        "average_cost": 0.0,
        "median_cost": 0.0,
        "maximum_cost": 0.0,
        "minimum_cost": 0.0,
        "cost_count": 0,
    }

    if costs_dataframe.empty:
        return empty_result

    costs = pd.to_numeric(costs_dataframe["cout_detecte"], errors="coerce").dropna()

    if costs.empty:
        return empty_result

    return {
        "total_cost": float(costs.sum()),
        "average_cost": float(costs.mean()),
        "median_cost": float(costs.median()),
        "maximum_cost": float(costs.max()),
        "minimum_cost": float(costs.min()),
        "cost_count": int(costs.count()),
    }
