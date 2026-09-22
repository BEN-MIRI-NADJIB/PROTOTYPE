import pandas as pd
import streamlit as st


def apply_filters(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe.copy()

    filtered_dataframe = dataframe.copy()

    with st.sidebar:
        st.divider()
        st.markdown("## Filtres")

        file_options = sorted(
            dataframe["fichier_source"].dropna().astype(str).unique().tolist()
        )
        selected_files = st.multiselect("Fichiers", options=file_options, default=file_options)

        if selected_files:
            filtered_dataframe = filtered_dataframe[
                filtered_dataframe["fichier_source"].astype(str).isin(selected_files)
            ]
        else:
            return filtered_dataframe.iloc[0:0]

        sheet_options = sorted(
            filtered_dataframe["feuille_source"].dropna().astype(str).unique().tolist()
        )
        selected_sheets = st.multiselect("Feuilles", options=sheet_options, default=sheet_options)

        if selected_sheets:
            filtered_dataframe = filtered_dataframe[
                filtered_dataframe["feuille_source"].astype(str).isin(selected_sheets)
            ]
        else:
            return filtered_dataframe.iloc[0:0]

        if "prototype" in filtered_dataframe.columns:
            prototype_options = sorted(
                filtered_dataframe["prototype"].dropna().astype(str).unique().tolist()
            )
            selected_prototypes = st.multiselect(
                "Prototypes",
                options=prototype_options,
                default=prototype_options,
            )

            if selected_prototypes:
                filtered_dataframe = filtered_dataframe[
                    filtered_dataframe["prototype"].astype(str).isin(selected_prototypes)
                ]
            else:
                return filtered_dataframe.iloc[0:0]

        search_value = st.text_input("Recherche", placeholder="P1, eDrive, Bosch...")

        if search_value:
            searchable_columns = [
                column
                for column in filtered_dataframe.columns
                if column not in {"id_ligne", "ligne_source"}
            ]
            searchable_dataframe = filtered_dataframe[searchable_columns].astype("string").fillna("")
            search_mask = searchable_dataframe.apply(
                lambda column: column.str.contains(
                    search_value,
                    case=False,
                    na=False,
                    regex=False,
                )
            ).any(axis=1)
            filtered_dataframe = filtered_dataframe[search_mask]

        numeric_columns = [
            column
            for column in filtered_dataframe.select_dtypes(include="number").columns.tolist()
            if column not in {"id_ligne", "ligne_source"}
        ]

        if numeric_columns:
            selected_numeric_column = st.selectbox(
                "Variable numerique",
                options=["Aucun filtre"] + numeric_columns,
            )

            if selected_numeric_column != "Aucun filtre":
                minimum_value = float(filtered_dataframe[selected_numeric_column].min())
                maximum_value = float(filtered_dataframe[selected_numeric_column].max())

                if minimum_value < maximum_value:
                    selected_range = st.slider(
                        "Plage de valeurs",
                        min_value=minimum_value,
                        max_value=maximum_value,
                        value=(minimum_value, maximum_value),
                    )
                    filtered_dataframe = filtered_dataframe[
                        filtered_dataframe[selected_numeric_column].between(
                            selected_range[0],
                            selected_range[1],
                        )
                    ]

        st.info(f"{len(filtered_dataframe):,} enregistrement(s) selectionne(s)")

    return filtered_dataframe
