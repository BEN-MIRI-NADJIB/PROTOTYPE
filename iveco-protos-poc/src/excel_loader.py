from io import BytesIO
from pathlib import Path

import pandas as pd


def make_unique_column_names(column_count):
    column_names = []

    for index in range(column_count):
        column_names.append("colonne_" + str(index + 1))

    return column_names


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

        file_content = file_payload.get("content")

        if file_content is None:
            file_content = file_payload.get("data")

        if file_content is None:
            file_content = file_payload.get("bytes")

        if file_content is None:
            file_content = file_payload.get("value")

        if file_content is None:
            file_content = file_payload.get("file")

    else:
        file_name = getattr(
            file_payload,
            "name",
            "fichier_excel.xlsx",
        )

        if hasattr(file_payload, "getvalue"):
            file_content = file_payload.getvalue()

        elif hasattr(file_payload, "read"):
            if hasattr(file_payload, "seek"):
                file_payload.seek(0)

            file_content = file_payload.read()

        elif isinstance(file_payload, bytes):
            file_content = file_payload

    if file_content is None:
        raise ValueError(
            "Le dictionnaire du fichier ne contient aucune donnée Excel."
        )

    if hasattr(file_content, "getvalue"):
        file_content = file_content.getvalue()

    elif hasattr(file_content, "read"):
        if hasattr(file_content, "seek"):
            file_content.seek(0)

        file_content = file_content.read()

    if isinstance(file_content, bytearray):
        file_content = bytes(file_content)

    if not isinstance(file_content, bytes):
        raise TypeError(
            "Le contenu du fichier doit être au format bytes."
        )

    clean_file_name = Path(str(file_name)).name
    excel_source = BytesIO(file_content)

    return clean_file_name, excel_source


def load_excel_file(file_payload):
    sheets = []
    errors = []

    try:
        file_name, excel_source = prepare_excel_file(
            file_payload
        )

        workbook = pd.ExcelFile(
            excel_source,
            engine="openpyxl",
        )

        for sheet_name in workbook.sheet_names:
            try:
                dataframe = pd.read_excel(
                    workbook,
                    sheet_name=sheet_name,
                    header=None,
                    dtype=object,
                )

                dataframe = dataframe.dropna(
                    axis=0,
                    how="all",
                )

                dataframe = dataframe.dropna(
                    axis=1,
                    how="all",
                )

                if dataframe.empty:
                    continue

                dataframe.columns = make_unique_column_names(
                    len(dataframe.columns)
                )

                dataframe.insert(
                    0,
                    "ligne_source",
                    range(1, len(dataframe) + 1),
                )

                dataframe.insert(
                    0,
                    "feuille_source",
                    sheet_name,
                )

                dataframe.insert(
                    0,
                    "fichier_source",
                    file_name,
                )

                sheets.append(
                    {
                        "file_name": file_name,
                        "sheet_name": sheet_name,
                        "dataframe": dataframe,
                    }
                )

            except Exception as error:
                errors.append(
                    "Impossible de lire la feuille "
                    + str(sheet_name)
                    + " du fichier "
                    + str(file_name)
                    + " : "
                    + str(error)
                )

        workbook.close()

    except Exception as error:
        errors.append(
            "Impossible d'ouvrir le fichier Excel : "
            + str(error)
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
        sheets, errors = load_excel_file(
            file_payload
        )

        all_sheets.extend(sheets)
        all_errors.extend(errors)

    return all_sheets, all_errors