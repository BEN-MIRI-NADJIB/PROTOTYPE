import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def format_number(value: float) -> str:
    return f"{value:,.1f}".replace(",", " ")


def create_quality_gauge(quality_score: float):
    if quality_score >= 85:
        gauge_color = "#15803d"
    elif quality_score >= 65:
        gauge_color = "#b45309"
    else:
        gauge_color = "#b91c1c"

    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=quality_score,
            number={"suffix": " %", "font": {"size": 34, "color": "#00334d"}},
            title={
                "text": "Score qualite des donnees",
                "font": {"size": 17, "color": "#334155"},
            },
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": gauge_color, "thickness": 0.30},
                "bgcolor": "#e2e8f0",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 65], "color": "#fee2e2"},
                    {"range": [65, 85], "color": "#fef3c7"},
                    {"range": [85, 100], "color": "#dcfce7"},
                ],
            },
        )
    )

    figure.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=55, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Segoe UI"},
    )

    return figure


def display_dashboard(
    dataframe: pd.DataFrame,
    validation_report: dict,
    cost_kpis: dict,
) -> None:
    st.markdown('<div class="section-title">Synthese executive</div>', unsafe_allow_html=True)

    file_count = dataframe["fichier_source"].nunique() if "fichier_source" in dataframe.columns else 0
    sheet_count = dataframe["feuille_source"].nunique() if "feuille_source" in dataframe.columns else 0
    prototype_count = dataframe["prototype"].nunique() if "prototype" in dataframe.columns else 0

    columns = st.columns(5)
    columns[0].metric("Fichiers", file_count)
    columns[1].metric("Feuilles", sheet_count)
    columns[2].metric("Prototypes", prototype_count)
    columns[3].metric("Cout total", f"{format_number(cost_kpis['total_cost'])} k€")
    columns[4].metric("Points DAP/CID", len(validation_report["issues"]))

    left_column, right_column = st.columns([1, 1.4])

    with left_column:
        st.plotly_chart(
            create_quality_gauge(validation_report["quality_score"]),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with right_column:
        st.markdown('<div class="section-title">Indicateurs couts</div>', unsafe_allow_html=True)
        first_row = st.columns(3)
        first_row[0].metric("Valeurs couts", cost_kpis["cost_count"])
        first_row[1].metric("Cout moyen", f"{format_number(cost_kpis['average_cost'])} k€")
        first_row[2].metric("Cout median", f"{format_number(cost_kpis['median_cost'])} k€")

        second_row = st.columns(2)
        second_row[0].metric("Cout minimum", f"{format_number(cost_kpis['minimum_cost'])} k€")
        second_row[1].metric("Cout maximum", f"{format_number(cost_kpis['maximum_cost'])} k€")

    if validation_report["quality_score"] >= 85:
        st.info("Qualite des donnees satisfaisante pour preparer l'export Power BI.")
    elif validation_report["quality_score"] >= 65:
        st.warning("Certaines donnees doivent etre revues avant validation finale DAP / CID.")
    else:
        st.warning("Controle necessaire avant exploitation: plusieurs anomalies peuvent impacter l'analyse.")
