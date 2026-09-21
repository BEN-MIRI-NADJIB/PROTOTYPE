import pandas as pd
import streamlit as st


def apply_filters(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe.copy()

    filtered_dataframe = dataframe.copy()

    with st.sidebar:
        st.divider()
        st.markdown("## Filtres intelligents")

        file_options = sorted(
            dataframe["fichier_source"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_files = st.multiselect(
            "Fichiers",
            options=file_options,
            default=file_options,
        )

        if selected_files:
            filtered_dataframe = filtered_dataframe[
                filtered_dataframe[
                    "fichier_source"
                ].astype(str).isin(selected_files)
            ]
        else:
            return filtered_dataframe.iloc[0:0]

        sheet_options = sorted(
            filtered_dataframe["feuille_source"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_sheets = st.multiselect(
            "Feuilles",
            options=sheet_options,
            default=sheet_options,
        )

        if selected_sheets:
            filtered_dataframe = filtered_dataframe[
                filtered_dataframe[
                    "feuille_source"
                ].astype(str).isin(selected_sheets)
            ]
        else:
            return filtered_dataframe.iloc[0:0]

        search_value = st.text_input(
            "Recherche globale",
            placeholder="P1, GEN4, LF 12M...",
        )

        if search_value:
            searchable_columns = [
                column
                for column in filtered_dataframe.columns
                if column not in {
                    "id_ligne",
                    "ligne_source",
                }
            ]

            searchable_dataframe = (
                filtered_dataframe[
                    searchable_columns
                ]
                .astype("string")
                .fillna("")
            )

            search_mask = searchable_dataframe.apply(
                lambda column: column.str.contains(
                    search_value,
                    case=False,
                    na=False,
                    regex=False,
                )
            ).any(axis=1)

            filtered_dataframe = filtered_dataframe[
                search_mask
            ]

        numeric_columns = filtered_dataframe.select_dtypes(
            include="number"
        ).columns.tolist()

        numeric_columns = [
            column
            for column in numeric_columns
            if column not in {
                "id_ligne",
                "ligne_source",
            }
        ]

        if numeric_columns:
            selected_numeric_column = st.selectbox(
                "Colonne numérique à filtrer",
                options=["Aucun filtre"] + numeric_columns,
            )

            if selected_numeric_column != "Aucun filtre":
                minimum_value = float(
                    filtered_dataframe[
                        selected_numeric_column
                    ].min()
                )

                maximum_value = float(
                    filtered_dataframe[
                        selected_numeric_column
                    ].max()
                )

                if minimum_value < maximum_value:
                    selected_range = st.slider(
                        "Plage de valeurs",
                        min_value=minimum_value,
                        max_value=maximum_value,
                        value=(
                            minimum_value,
                            maximum_value,
                        ),
                    )

                    filtered_dataframe = (
                        filtered_dataframe[
                            filtered_dataframe[
                                selected_numeric_column
                            ].between(
                                selected_range[0],
                                selected_range[1],
                            )
                        ]
                    )

        st.info(
            f"{len(filtered_dataframe):,} ligne(s) sélectionnée(s)"
        )

    return filtered_dataframe