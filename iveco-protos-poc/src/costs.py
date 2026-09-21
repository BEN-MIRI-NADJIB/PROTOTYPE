import re
import unicodedata

import pandas as pd


COST_KEYWORDS = (
    "cost",
    "cout",
    "coût",
    "budget",
    "price",
    "prix",
    "material",
    "assembly",
    "amortization",
    "amortissement",
    "total",
)


def normalize_value(value) -> str:
    if pd.isna(value):
        return ""

    normalized_value = unicodedata.normalize(
        "NFKD",
        str(value),
    )

    return normalized_value.encode(
        "ascii",
        "ignore",
    ).decode("ascii").lower().strip()


def contains_cost_keyword(value) -> bool:
    normalized_value = normalize_value(value)

    normalized_keywords = [
        normalize_value(keyword)
        for keyword in COST_KEYWORDS
    ]

    return any(
        keyword in normalized_value
        for keyword in normalized_keywords
    )


def extract_number(value):
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text_value = str(value).strip()

    text_value = (
        text_value
        .replace("\u00a0", "")
        .replace("k€", "")
        .replace("€", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    if not re.fullmatch(
        r"-?\d+(?:\.\d+)?",
        text_value,
    ):
        return None

    try:
        return float(text_value)
    except ValueError:
        return None


def extract_costs(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame()

    metadata_columns = [
        column
        for column in [
            "id_ligne",
            "fichier_source",
            "feuille_source",
            "ligne_source",
        ]
        if column in dataframe.columns
    ]

    data_columns = [
        column
        for column in dataframe.columns
        if column not in metadata_columns
    ]

    numeric_columns = dataframe[
        data_columns
    ].select_dtypes(
        include="number"
    ).columns.tolist()

    extracted_costs = []

    for row in dataframe.itertuples(index=False):
        row_dictionary = row._asdict()

        labels = [
            str(row_dictionary.get(column))
            for column in data_columns
            if contains_cost_keyword(
                row_dictionary.get(column)
            )
        ]

        if not labels:
            continue

        for column in numeric_columns:
            numeric_value = extract_number(
                row_dictionary.get(column)
            )

            if numeric_value is None:
                continue

            extracted_costs.append(
                {
                    "id_ligne": row_dictionary.get(
                        "id_ligne"
                    ),
                    "fichier_source": row_dictionary.get(
                        "fichier_source"
                    ),
                    "feuille_source": row_dictionary.get(
                        "feuille_source"
                    ),
                    "ligne_source": row_dictionary.get(
                        "ligne_source"
                    ),
                    "libelle_cout": " | ".join(
                        labels[:3]
                    ),
                    "colonne_cout": column,
                    "cout_detecte": numeric_value,
                }
            )

    return pd.DataFrame(extracted_costs)


def calculate_cost_kpis(
    costs_dataframe: pd.DataFrame,
) -> dict:
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

    costs = pd.to_numeric(
        costs_dataframe["cout_detecte"],
        errors="coerce",
    ).dropna()

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