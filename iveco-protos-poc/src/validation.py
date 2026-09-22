import pandas as pd


METADATA_COLUMNS = {"id_ligne", "fichier_source", "feuille_source", "ligne_source"}


def build_issue(
    row_id,
    file_name,
    sheet_name,
    source_row,
    issue_type,
    column_name,
    value,
    description,
    severity,
):
    return {
        "id_ligne": row_id,
        "fichier_source": file_name,
        "feuille_source": sheet_name,
        "ligne_source": source_row,
        "severite": severity,
        "type_anomalie": issue_type,
        "variable": column_name,
        "valeur": value,
        "message": description,
    }


def validate_dataframe(dataframe: pd.DataFrame) -> dict:
    empty_report = {
        "total_rows": 0,
        "duplicate_rows": 0,
        "missing_cells": 0,
        "negative_values": 0,
        "quality_score": 100.0,
        "issues": pd.DataFrame(),
    }

    if dataframe.empty:
        return empty_report

    issues = []
    data_columns = [column for column in dataframe.columns if column not in METADATA_COLUMNS]

    if not data_columns:
        report = empty_report.copy()
        report["total_rows"] = len(dataframe)
        return report

    duplicate_mask = dataframe.duplicated(subset=data_columns, keep=False)
    duplicate_rows = int(duplicate_mask.sum())
    duplicate_data = dataframe.loc[
        duplicate_mask,
        [
            column
            for column in ["id_ligne", "fichier_source", "feuille_source", "ligne_source"]
            if column in dataframe.columns
        ],
    ]

    for row in duplicate_data.itertuples(index=False):
        row_dict = row._asdict()
        issues.append(
            build_issue(
                row_id=row_dict.get("id_ligne"),
                file_name=row_dict.get("fichier_source"),
                sheet_name=row_dict.get("feuille_source"),
                source_row=row_dict.get("ligne_source"),
                issue_type="Doublon",
                column_name="donnees_metier",
                value="",
                description="Cette information apparait plusieurs fois dans les donnees consolidees.",
                severity="Moyenne",
            )
        )

    missing_cells = int(dataframe[data_columns].isna().sum().sum())
    numeric_columns = dataframe[data_columns].select_dtypes(include="number").columns.tolist()
    negative_values = 0

    for column in numeric_columns:
        negative_mask = dataframe[column].lt(0)
        negative_values += int(negative_mask.sum())
        negative_rows = dataframe.loc[
            negative_mask,
            [
                column_name
                for column_name in [
                    "id_ligne",
                    "fichier_source",
                    "feuille_source",
                    "ligne_source",
                    column,
                ]
                if column_name in dataframe.columns
            ],
        ]

        for row in negative_rows.itertuples(index=False):
            row_dict = row._asdict()
            issues.append(
                build_issue(
                    row_id=row_dict.get("id_ligne"),
                    file_name=row_dict.get("fichier_source"),
                    sheet_name=row_dict.get("feuille_source"),
                    source_row=row_dict.get("ligne_source"),
                    issue_type="Valeur negative",
                    column_name=column,
                    value=row_dict.get(column),
                    description="Montant negatif a verifier dans DAP ou CID avant export Power BI.",
                    severity="Haute",
                )
            )

    total_cells = max(len(dataframe) * len(data_columns), 1)
    missing_ratio = missing_cells / total_cells
    duplicate_ratio = duplicate_rows / max(len(dataframe), 1)
    negative_ratio = negative_values / total_cells
    penalty = missing_ratio * 45 + duplicate_ratio * 35 + negative_ratio * 20
    quality_score = max(0.0, min(100.0, 100.0 - penalty))

    return {
        "total_rows": len(dataframe),
        "duplicate_rows": duplicate_rows,
        "missing_cells": missing_cells,
        "negative_values": negative_values,
        "quality_score": quality_score,
        "issues": pd.DataFrame(issues),
    }
