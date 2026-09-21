import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def format_number(value: float) -> str:
    return f"{value:,.1f}".replace(",", " ")


def create_quality_gauge(
    quality_score: float,
):
    if quality_score >= 85:
        gauge_color = "#16a34a"
    elif quality_score >= 65:
        gauge_color = "#f59e0b"
    else:
        gauge_color = "#dc2626"

    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=quality_score,
            number={
                "suffix": " %",
                "font": {
                    "size": 40,
                    "color": "#003b5c",
                },
            },
            title={
                "text": "Score qualité des données",
                "font": {
                    "size": 20,
                    "color": "#334155",
                },
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                },
                "bar": {
                    "color": gauge_color,
                    "thickness": 0.32,
                },
                "bgcolor": "#e2e8f0",
                "borderwidth": 0,
                "steps": [
                    {
                        "range": [0, 65],
                        "color": "#fee2e2",
                    },
                    {
                        "range": [65, 85],
                        "color": "#fef3c7",
                    },
                    {
                        "range": [85, 100],
                        "color": "#dcfce7",
                    },
                ],
            },
        )
    )

    figure.update_layout(
        height=310,
        margin=dict(
            l=30,
            r=30,
            t=60,
            b=20,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Arial",
        },
        transition={
            "duration": 500,
        },
    )

    return figure


def display_dashboard(
    dataframe: pd.DataFrame,
    validation_report: dict,
    cost_kpis: dict,
) -> None:
    st.markdown(
        '<div class="section-title">Synthèse exécutive</div>',
        unsafe_allow_html=True,
    )

    file_count = (
        dataframe["fichier_source"].nunique()
        if "fichier_source" in dataframe.columns
        else 0
    )

    sheet_count = (
        dataframe["feuille_source"].nunique()
        if "feuille_source" in dataframe.columns
        else 0
    )

    columns = st.columns(5)

    columns[0].metric(
        "Fichiers",
        file_count,
    )

    columns[1].metric(
        "Feuilles",
        sheet_count,
    )

    columns[2].metric(
        "Lignes",
        f"{len(dataframe):,}",
    )

    columns[3].metric(
        "Coût détecté",
        f"{format_number(cost_kpis['total_cost'])} k€",
    )

    columns[4].metric(
        "Anomalies",
        len(validation_report["issues"]),
    )

    left_column, right_column = st.columns(
        [1, 1.35]
    )

    with left_column:
        quality_gauge = create_quality_gauge(
            validation_report["quality_score"]
        )

        st.plotly_chart(
            quality_gauge,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

    with right_column:
        st.markdown(
            '<div class="section-title">Analyse des coûts</div>',
            unsafe_allow_html=True,
        )

        first_row = st.columns(3)

        first_row[0].metric(
            "Valeurs détectées",
            cost_kpis["cost_count"],
        )

        first_row[1].metric(
            "Coût moyen",
            f"{format_number(cost_kpis['average_cost'])} k€",
        )

        first_row[2].metric(
            "Coût médian",
            f"{format_number(cost_kpis['median_cost'])} k€",
        )

        second_row = st.columns(2)

        second_row[0].metric(
            "Coût minimum",
            f"{format_number(cost_kpis['minimum_cost'])} k€",
        )

        second_row[1].metric(
            "Coût maximum",
            f"{format_number(cost_kpis['maximum_cost'])} k€",
        )

    if validation_report["quality_score"] >= 85:
        st.success(
            "La qualité générale des données est satisfaisante."
        )
    elif validation_report["quality_score"] >= 65:
        st.warning(
            "La qualité des données est correcte, mais certaines "
            "lignes nécessitent une vérification."
        )
    else:
        st.error(
            "La qualité des données nécessite une vérification "
            "avant utilisation dans Power BI."
        )