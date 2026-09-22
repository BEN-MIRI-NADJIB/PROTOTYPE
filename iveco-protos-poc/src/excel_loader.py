from io import BytesIO
from pathlib import Path
import re
import unicodedata

import pandas as pd


MONTH_LABELS = {
    "j": "janvier",
    "f": "fevrier",
    "m": "mars",
    "a": "avril",
    "s": "septembre",
    "o": "octobre",
    "n": "novembre",
    "d": "decembre",
}

MONTH_NAMES_BY_POSITION = [
    "janvier",
    "fevrier",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "aout",
    "septembre",
    "octobre",
    "novembre",
    "decembre",
]


def normalize_label(value) -> str:
    if pd.isna(value):
        return ""

    normalized = unicodedata.normalize("NFKD", str(value))
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    return normalized


def slugify(value, fallback: str) -> str:
    label = normalize_label(value)
    label = re.sub(r"[^a-z0-9]+", "_", label).strip("_")
    return label or fallback


def make_unique_column_names(columns):
    counters = {}
    unique_columns = []

    for column in columns:
        if column not in counters:
            counters[column] = 1
            unique_columns.append(column)
            continue

        counters[column] += 1
        unique_columns.append(f"{column}_{counters[column]}")

    return unique_columns


def prepare_excel_file(file_payload):
    file_name = "fichier_excel.xlsx"
    file_content = None

    if isinstance(file_payload, dict):
        file_name = (
            file_payload.get("name")
            or file_payload.get("file_name")
            or file_payload.get("filename")
            or "fichier_excel.xlsx"
        )
        file_content = (
            file_payload.get("content")
            or file_payload.get("data")
            or file_payload.get("bytes")
            or file_payload.get("value")
            or file_payload.get("file")
        )
    else:
        file_name = getattr(file_payload, "name", "fichier_excel.xlsx")

        if hasattr(file_payload, "getvalue"):
            file_content = file_payload.getvalue()
        elif hasattr(file_payload, "read"):
            if hasattr(file_payload, "seek"):
                file_payload.seek(0)
            file_content = file_payload.read()
        elif isinstance(file_payload, bytes):
            file_content = file_payload

    if file_content is None:
        raise ValueError("Le fichier importe ne contient aucune donnee Excel lisible.")

    if hasattr(file_content, "getvalue"):
        file_content = file_content.getvalue()
    elif hasattr(file_content, "read"):
        if hasattr(file_content, "seek"):
            file_content.seek(0)
        file_content = file_content.read()

    if isinstance(file_content, bytearray):
        file_content = bytes(file_content)

    if not isinstance(file_content, bytes):
        raise TypeError("Le contenu du fichier doit etre un fichier Excel valide.")

    return Path(str(file_name)).name, BytesIO(file_content)


def find_prototype_header_rows(raw_dataframe: pd.DataFrame):
    normalized_rows = raw_dataframe.astype("object").where(pd.notna(raw_dataframe), "").map(normalize_label)

    for row_index in range(len(normalized_rows)):
        row_values = normalized_rows.iloc[row_index].tolist()
        has_piece_price = any("piece price" in value for value in row_values)
        has_cost = any("cost" in value or "cout" in value for value in row_values)
        has_quantity = any(value in {"nb", "qty", "quantity"} for value in row_values)

        if has_piece_price and has_cost and has_quantity:
            return max(row_index - 2, 0), max(row_index - 1, 0), row_index

    return None


def find_budget_header_rows(raw_dataframe: pd.DataFrame):
    normalized_rows = raw_dataframe.astype("object").where(pd.notna(raw_dataframe), "").map(normalize_label)

    for row_index in range(min(len(normalized_rows), 8)):
        row_values = normalized_rows.iloc[row_index].tolist()
        has_designation = any("designation" in value for value in row_values)
        has_budget_year = any("2026" in value or "budget" in value for value in row_values)

        if has_designation and has_budget_year:
            return row_index, row_index + 1

    return None


def find_proto_plan_header_row(raw_dataframe: pd.DataFrame):
    normalized_rows = raw_dataframe.astype("object").where(pd.notna(raw_dataframe), "").map(normalize_label)

    for row_index in range(min(len(normalized_rows), 12)):
        row_values = normalized_rows.iloc[row_index].tolist()
        has_proto = any(value == "proto" for value in row_values)
        has_total_cost = any("total cost" in value or "total cout" in value for value in row_values)
        has_material = any("material" in value for value in row_values)

        if has_proto and has_total_cost and has_material:
            return row_index

    return None


def build_proto_plan_records(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    header_row = find_proto_plan_header_row(raw_dataframe)
    if header_row is None:
        return pd.DataFrame()

    records = []
    header_values = raw_dataframe.iloc[header_row].tolist()
    data_start = header_row + 1

    fixed_columns = {
        "projet": 0,
        "hypothese": 1,
        "type_proto": 2,
        "generation_batterie": 3,
        "prototype": 4,
        "assemblage": 5,
        "matiere_ke": 6,
        "management_reseau_pe_ke": 7,
        "assemblage_squelette_ke": 8,
        "assemblage_vehicule_ke": 9,
        "amortissement_vehicule_ke": 10,
        "cout_ke": 11,
        "couverture_budget_ke": 12,
        "commentaire": 13,
        "assembly": 14,
        "id_prototype": 15,
    }

    timeline_start = 16
    week_labels = {}

    if raw_dataframe.shape[0] > 2:
        for column_index in range(timeline_start, raw_dataframe.shape[1]):
            week_value = raw_dataframe.iat[2, column_index]
            if not pd.isna(week_value):
                week_labels[column_index] = str(week_value).strip()

    for row_index in range(data_start, len(raw_dataframe)):
        row = raw_dataframe.iloc[row_index]
        if row.dropna().empty:
            continue

        project_value = row.iloc[0] if raw_dataframe.shape[1] > 0 else pd.NA
        prototype_value = row.iloc[4] if raw_dataframe.shape[1] > 4 else pd.NA
        total_cost = row.iloc[11] if raw_dataframe.shape[1] > 11 else pd.NA

        if pd.isna(project_value) and pd.isna(prototype_value) and pd.isna(total_cost):
            continue

        record = {
            output_name: row.iloc[column_index]
            if column_index < raw_dataframe.shape[1]
            else pd.NA
            for output_name, column_index in fixed_columns.items()
        }

        planned_weeks = []
        for column_index in range(timeline_start, raw_dataframe.shape[1]):
            cell_value = row.iloc[column_index]
            if pd.isna(cell_value):
                continue

            planned_weeks.append(
                f"S{week_labels.get(column_index, column_index - timeline_start + 1)}:{cell_value}"
            )

        record["planning_semaines"] = " | ".join(planned_weeks)
        record["ligne_source"] = row_index + 1
        records.append(record)

    return pd.DataFrame(records)


def build_budget_records(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    header_rows = find_budget_header_rows(raw_dataframe)
    if header_rows is None:
        return pd.DataFrame()

    title_row, month_row = header_rows
    data_start = month_row + 1
    records = []

    month_columns = []
    for column_index in range(4, raw_dataframe.shape[1]):
        month_candidate = normalize_label(raw_dataframe.iat[month_row, column_index])
        if month_candidate not in MONTH_LABELS:
            continue

        month_position = len(month_columns)
        month_name = MONTH_NAMES_BY_POSITION[month_position % len(MONTH_NAMES_BY_POSITION)]
        month_columns.append(
            (
                column_index,
                month_name,
                month_position + 1,
            )
        )

    if not month_columns:
        return pd.DataFrame()

    current_system = pd.NA

    for row_index in range(data_start, len(raw_dataframe)):
        row = raw_dataframe.iloc[row_index]
        if row.dropna().empty:
            continue

        if not pd.isna(row.iloc[0]):
            current_system = row.iloc[0]

        designation = row.iloc[1] if raw_dataframe.shape[1] > 1 else pd.NA
        budget_2026_ke = row.iloc[1] if raw_dataframe.shape[1] > 1 else pd.NA
        montant_planifie_ke = row.iloc[2] if raw_dataframe.shape[1] > 2 else pd.NA
        fournisseur = row.iloc[3] if raw_dataframe.shape[1] > 3 else pd.NA

        for column_index, month_name, month_sequence in month_columns:
            monthly_cost = row.iloc[column_index]

            if pd.isna(monthly_cost):
                continue

            records.append(
                {
                    "systeme": current_system,
                    "designation": designation,
                    "fournisseur": fournisseur,
                    "prototype": "Budget 2026",
                    "mois": month_name,
                    "sequence_mois": month_sequence,
                    "budget_2026_ke": budget_2026_ke,
                    "montant_planifie_ke": montant_planifie_ke,
                    "cout_ke": monthly_cost,
                    "ligne_source": row_index + 1,
                }
            )

    return pd.DataFrame(records)


def build_prototype_records(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    header_rows = find_prototype_header_rows(raw_dataframe)
    if header_rows is None:
        return pd.DataFrame()

    family_row, prototype_row, metric_row = header_rows
    data_start = metric_row + 1
    records = []

    prototype_context = {}
    current_prototype = ""

    for column_index in range(raw_dataframe.shape[1]):
        candidate = raw_dataframe.iat[prototype_row, column_index]
        if normalize_label(candidate):
            current_prototype = str(candidate).strip()
        prototype_context[column_index] = current_prototype

    for row_index in range(data_start, len(raw_dataframe)):
        row = raw_dataframe.iloc[row_index]
        if row.dropna().empty:
            continue

        systeme = row.iloc[0] if raw_dataframe.shape[1] > 0 else pd.NA
        composant = row.iloc[1] if raw_dataframe.shape[1] > 1 else pd.NA
        prix_piece_ke = row.iloc[2] if raw_dataframe.shape[1] > 2 else pd.NA

        if pd.isna(composant):
            continue

        base_record = {
            "systeme": systeme,
            "composant": composant,
            "prix_piece_ke": prix_piece_ke,
        }

        metric_columns = []

        for column_index in range(3, raw_dataframe.shape[1]):
            metric_name = normalize_label(raw_dataframe.iat[metric_row, column_index])
            if metric_name in {"nb", "qty", "quantity"}:
                metric_columns.append((column_index, "quantite"))
            elif "cost" in metric_name or "cout" in metric_name:
                metric_columns.append((column_index, "cout_ke"))

        if not metric_columns:
            continue

        grouped_values = {}
        for column_index, metric_name in metric_columns:
            prototype = prototype_context.get(column_index) or "prototype_non_precise"
            grouped_values.setdefault(prototype, {}).update(
                {metric_name: row.iloc[column_index]}
            )

        for prototype, values in grouped_values.items():
            if pd.isna(values.get("quantite")) and pd.isna(values.get("cout_ke")):
                continue

            records.append(
                {
                    **base_record,
                    "prototype": prototype,
                    "quantite": values.get("quantite", pd.NA),
                    "cout_ke": values.get("cout_ke", pd.NA),
                    "commentaire": row.iloc[-1] if raw_dataframe.shape[1] else pd.NA,
                    "ligne_source": row_index + 1,
                }
            )

    return pd.DataFrame(records)


def find_generic_header_row(raw_dataframe: pd.DataFrame) -> int:
    best_row_index = 0
    best_score = -1

    for row_index in range(min(len(raw_dataframe), 12)):
        row = raw_dataframe.iloc[row_index]
        non_empty_count = int(row.notna().sum())
        text_count = sum(
            1
            for value in row
            if isinstance(value, str) and normalize_label(value)
        )
        score = text_count * 2 + non_empty_count

        if score > best_score:
            best_score = score
            best_row_index = row_index

    return best_row_index


def build_generic_dataframe(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    header_row = find_generic_header_row(raw_dataframe)
    header_values = raw_dataframe.iloc[header_row].tolist()
    columns = [
        slugify(value, f"variable_{index + 1}")
        for index, value in enumerate(header_values)
    ]

    dataframe = raw_dataframe.iloc[header_row + 1 :].copy()
    dataframe.columns = make_unique_column_names(columns)
    dataframe = dataframe.dropna(axis=0, how="all")
    dataframe = dataframe.dropna(axis=1, how="all")
    dataframe["ligne_source"] = dataframe.index + 1

    return dataframe.reset_index(drop=True)


def normalize_sheet_dataframe(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    raw_dataframe = raw_dataframe.dropna(axis=0, how="all")
    raw_dataframe = raw_dataframe.dropna(axis=1, how="all")

    if raw_dataframe.empty:
        return pd.DataFrame()

    proto_plan_dataframe = build_proto_plan_records(raw_dataframe)
    if not proto_plan_dataframe.empty:
        return proto_plan_dataframe

    budget_dataframe = build_budget_records(raw_dataframe)
    if not budget_dataframe.empty:
        return budget_dataframe

    prototype_dataframe = build_prototype_records(raw_dataframe)
    if not prototype_dataframe.empty:
        return prototype_dataframe

    return build_generic_dataframe(raw_dataframe)


def load_excel_file(file_payload):
    sheets = []
    errors = []

    try:
        file_name, excel_source = prepare_excel_file(file_payload)
        workbook = pd.ExcelFile(excel_source, engine="openpyxl")

        for sheet_name in workbook.sheet_names:
            try:
                raw_dataframe = pd.read_excel(
                    workbook,
                    sheet_name=sheet_name,
                    header=None,
                    dtype=object,
                )

                dataframe = normalize_sheet_dataframe(raw_dataframe)

                if dataframe.empty:
                    continue

                dataframe.insert(0, "feuille_source", sheet_name)
                dataframe.insert(0, "fichier_source", file_name)

                sheets.append(
                    {
                        "file_name": file_name,
                        "sheet_name": sheet_name,
                        "dataframe": dataframe,
                    }
                )

            except Exception:
                errors.append(
                    "La feuille "
                    + str(sheet_name)
                    + " du fichier "
                    + str(file_name)
                    + " n'a pas pu etre lue. Verifiez que la feuille n'est pas protegee ou vide."
                )

        workbook.close()

    except Exception:
        errors.append(
            "Le fichier Excel n'a pas pu etre ouvert. Verifiez le format du fichier puis reimportez-le."
        )

    return sheets, errors


def load_excel_files(files_payload):
    all_sheets = []
    all_errors = []

    if files_payload is None:
        return all_sheets, all_errors

    if isinstance(files_payload, dict):
        files_payload = [files_payload]

    for file_payload in files_payload:
        sheets, errors = load_excel_file(file_payload)
        all_sheets.extend(sheets)
        all_errors.extend(errors)

    return all_sheets, all_errors
