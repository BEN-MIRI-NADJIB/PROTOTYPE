import re
import unicodedata

import numpy as np
import pandas as pd


EMPTY_VALUES = {
    "",
    "-",
    "--",
    "n/a",
    "na",
    "nan",
    "none",
    "null",
}


def normalize_text(value):
    if not isinstance(value, str):
        return value

    cleaned_value = re.sub(
        r"\s+",
        " ",
        value.replace("\u00a0", " "),
    ).strip()

    if cleaned_value.lower() in EMPTY_VALUES:
        return pd.NA

    return cleaned_value


def normalize_column_name(column_name: str) -> str:
    normalized_name = unicodedata.normalize(
        "NFKD",
        str(column_name),
    )

    normalized_name = normalized_name.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    normalized_name = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        normalized_name.lower(),
    ).strip("_")

    return normalized_name or "colonne"


def ensure_unique_columns(columns):
    counters = {}
    unique_columns = []

    for column in columns:
        if column not in counters:
            counters[column] = 1
            unique_columns.append(column)
        else:
            counters[column] += 1
            unique_columns.append(
                f"{column}_{counters[column]}"
            )

    return unique_columns


def convert_numeric_values(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    result = dataframe.copy()

    metadata_columns = {
        "fichier_source",
        "feuille_source",
        "ligne_source",
    }

    for column in result.columns:
        if column in metadata_columns:
            continue

        series = result[column]

        if pd.api.types.is_numeric_dtype(series):
            continue

        prepared_values = (
            series.astype("string")
            .str.replace("\u00a0", "", regex=False)
            .str.replace("k€", "", regex=False)
            .str.replace("€", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )

        numeric_values = pd.to_numeric(
            prepared_values,
            errors="coerce",
        )

        non_empty_count = int(series.notna().sum())

        if non_empty_count == 0:
            continue

        numeric_count = int(numeric_values.notna().sum())
        numeric_ratio = numeric_count / non_empty_count

        if numeric_ratio >= 0.70:
            result[column] = numeric_values

    return result


def clean_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe.copy()

    cleaned_dataframe = dataframe.copy()

    normalized_columns = [
        normalize_column_name(column)
        for column in cleaned_dataframe.columns
    ]

    cleaned_dataframe.columns = ensure_unique_columns(
        normalized_columns
    )

    object_columns = cleaned_dataframe.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in object_columns:
        cleaned_dataframe[column] = (
            cleaned_dataframe[column]
            .map(normalize_text)
        )

    data_columns = [
        column
        for column in cleaned_dataframe.columns
        if column not in {
            "fichier_source",
            "feuille_source",
            "ligne_source",
        }
    ]

    if data_columns:
        cleaned_dataframe = cleaned_dataframe.dropna(
            subset=data_columns,
            how="all",
        )

    cleaned_dataframe = convert_numeric_values(
        cleaned_dataframe
    )

    cleaned_dataframe = cleaned_dataframe.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    cleaned_dataframe = cleaned_dataframe.reset_index(
        drop=True
    )

    cleaned_dataframe.insert(
        0,
        "id_ligne",
        np.arange(
            1,
            len(cleaned_dataframe) + 1,
            dtype=int,
        ),
    )

    return cleaned_dataframe