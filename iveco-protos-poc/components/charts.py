import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


IVECO_COLORS = [
    "#00334d",
    "#006f95",
    "#00a3bd",
    "#2f855a",
    "#64748b",
    "#b45309",
    "#7c3aed",
    "#b91c1c",
]


def apply_professional_layout(figure, title: str):
    figure.update_layout(
        title={
            "text": title,
            "x": 0.01,
            "xanchor": "left",
            "font": {"size": 18, "color": "#00334d"},
        },
        font={"family": "Segoe UI", "color": "#334155"},
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="#f8fafc",
        hoverlabel={"bgcolor": "white", "font_size": 12},
        margin=dict(l=50, r=30, t=70, b=70),
        legend={
            "title": "",
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        uniformtext_minsize=10,
        uniformtext_mode="hide",
    )

    figure.update_xaxes(showgrid=False, linecolor="#cbd5e1", automargin=True, tickangle=-20)
    figure.update_yaxes(gridcolor="#e2e8f0", zeroline=False, automargin=True)
    return figure


def create_rows_by_sheet_chart(dataframe: pd.DataFrame):
    summary = (
        dataframe.groupby(["fichier_source", "feuille_source"], dropna=False)
        .size()
        .reset_index(name="enregistrements")
        .sort_values("enregistrements", ascending=False)
    )

    figure = px.bar(
        summary,
        x="feuille_source",
        y="enregistrements",
        color="fichier_source",
        barmode="group",
        color_discrete_sequence=IVECO_COLORS,
        text_auto=True,
        hover_data={"fichier_source": True, "feuille_source": True, "enregistrements": ":,"},
    )

    figure.update_traces(
        marker_line_width=0,
        opacity=0.92,
        hovertemplate="<b>%{x}</b><br>Enregistrements : %{y:,}<br><extra></extra>",
    )

    return apply_professional_layout(figure, "Volume consolide par feuille")


def create_cost_by_sheet_chart(costs_dataframe: pd.DataFrame):
    summary = (
        costs_dataframe.groupby(["fichier_source", "feuille_source"], dropna=False)["cout_detecte"]
        .sum()
        .reset_index()
        .sort_values("cout_detecte", ascending=False)
    )

    figure = px.bar(
        summary,
        x="feuille_source",
        y="cout_detecte",
        color="fichier_source",
        color_discrete_sequence=IVECO_COLORS,
        text_auto=".3s",
        hover_data={"cout_detecte": ":,.2f"},
    )

    figure.update_traces(
        marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>Cout detecte : %{y:,.2f} k€<br><extra></extra>",
    )

    return apply_professional_layout(figure, "Couts detectes par feuille")


def create_cost_distribution_chart(costs_dataframe: pd.DataFrame):
    figure = px.histogram(
        costs_dataframe,
        x="cout_detecte",
        color="feuille_source",
        nbins=35,
        marginal="box",
        color_discrete_sequence=IVECO_COLORS,
        hover_data=["fichier_source", "feuille_source", "libelle_cout"],
    )

    figure.update_traces(opacity=0.78)
    return apply_professional_layout(figure, "Distribution des couts")


def create_cost_boxplot(costs_dataframe: pd.DataFrame):
    figure = px.box(
        costs_dataframe,
        x="feuille_source",
        y="cout_detecte",
        color="feuille_source",
        points="outliers",
        color_discrete_sequence=IVECO_COLORS,
        hover_data=["fichier_source", "libelle_cout"],
    )

    return apply_professional_layout(figure, "Dispersion des couts")


def create_cost_treemap(costs_dataframe: pd.DataFrame):
    prepared_dataframe = costs_dataframe.copy()
    prepared_dataframe["cout_absolu"] = prepared_dataframe["cout_detecte"].abs()
    prepared_dataframe = prepared_dataframe[prepared_dataframe["cout_absolu"] > 0]

    if prepared_dataframe.empty:
        return None

    path_columns = [
        column
        for column in ["fichier_source", "feuille_source", "systeme", "composant", "prototype"]
        if column in prepared_dataframe.columns
    ]

    figure = px.treemap(
        prepared_dataframe,
        path=path_columns,
        values="cout_absolu",
        color="cout_detecte",
        color_continuous_scale=["#dbeafe", "#0284c7", "#00334d"],
        hover_data={"cout_detecte": ":,.2f", "cout_absolu": False},
    )

    figure.update_traces(textinfo="label+value+percent parent", textfont_size=12)
    return apply_professional_layout(figure, "Repartition hierarchique des couts")


def create_top_costs_chart(costs_dataframe: pd.DataFrame):
    top_costs = costs_dataframe.nlargest(20, "cout_detecte").sort_values("cout_detecte").copy()
    top_costs["description"] = top_costs["libelle_cout"].astype(str).str.slice(0, 70)

    figure = px.bar(
        top_costs,
        x="cout_detecte",
        y="description",
        orientation="h",
        color="cout_detecte",
        color_continuous_scale=["#bae6fd", "#0284c7", "#00334d"],
        text_auto=".3s",
        hover_data={
            "fichier_source": True,
            "feuille_source": True,
            "libelle_cout": True,
            "cout_detecte": ":,.2f",
            "description": False,
        },
    )

    figure.update_layout(height=650, showlegend=False)
    return apply_professional_layout(figure, "Top 20 des couts detectes")


def create_sheet_share_chart(dataframe: pd.DataFrame):
    summary = (
        dataframe["feuille_source"]
        .value_counts(dropna=False)
        .rename_axis("feuille_source")
        .reset_index(name="enregistrements")
    )

    figure = go.Figure(
        data=[
            go.Pie(
                labels=summary["feuille_source"],
                values=summary["enregistrements"],
                hole=0.62,
                marker={"colors": IVECO_COLORS, "line": {"color": "white", "width": 2}},
                textinfo="percent",
                hovertemplate="<b>%{label}</b><br>Enregistrements : %{value:,}<br>Part : %{percent}<br><extra></extra>",
            )
        ]
    )

    figure.add_annotation(
        text=f"{len(dataframe):,}<br>records",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 18, "color": "#00334d"},
    )

    return apply_professional_layout(figure, "Repartition par feuille")


def create_numeric_correlation_chart(dataframe: pd.DataFrame):
    numeric_dataframe = dataframe.select_dtypes(include="number").drop(
        columns=[
            column
            for column in ["id_ligne", "ligne_source"]
            if column in dataframe.columns
        ],
        errors="ignore",
    )

    if numeric_dataframe.shape[1] < 2:
        return None

    numeric_dataframe = numeric_dataframe.iloc[:, :20]
    correlation = numeric_dataframe.corr()

    figure = px.imshow(
        correlation,
        text_auto=".2f",
        color_continuous_scale=["#b91c1c", "#f8fafc", "#0369a1"],
        zmin=-1,
        zmax=1,
        aspect="auto",
    )

    return apply_professional_layout(figure, "Correlations entre variables numeriques")


def display_detailed_charts(dataframe: pd.DataFrame, costs_dataframe: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">Analyse detaillee</div>', unsafe_allow_html=True)

    volume_tab, cost_tab, statistical_tab = st.tabs(
        ["Volumes", "Couts", "Analyse statistique"]
    )

    plotly_config = {
        "displaylogo": False,
        "responsive": True,
        "scrollZoom": True,
        "modeBarButtonsToRemove": ["lasso2d"],
    }

    with volume_tab:
        first_column, second_column = st.columns([1.35, 1])

        with first_column:
            st.plotly_chart(
                create_rows_by_sheet_chart(dataframe),
                use_container_width=True,
                config=plotly_config,
            )

        with second_column:
            st.plotly_chart(
                create_sheet_share_chart(dataframe),
                use_container_width=True,
                config=plotly_config,
            )

    with cost_tab:
        if costs_dataframe.empty:
            st.info("Aucune donnee de cout detectee pour les filtres selectionnes.")
        else:
            st.plotly_chart(
                create_cost_by_sheet_chart(costs_dataframe),
                use_container_width=True,
                config=plotly_config,
            )

            first_column, second_column = st.columns(2)

            with first_column:
                st.plotly_chart(
                    create_cost_distribution_chart(costs_dataframe),
                    use_container_width=True,
                    config=plotly_config,
                )

            with second_column:
                st.plotly_chart(
                    create_cost_boxplot(costs_dataframe),
                    use_container_width=True,
                    config=plotly_config,
                )

            treemap_chart = create_cost_treemap(costs_dataframe)
            if treemap_chart is not None:
                st.plotly_chart(treemap_chart, use_container_width=True, config=plotly_config)

            st.plotly_chart(
                create_top_costs_chart(costs_dataframe),
                use_container_width=True,
                config=plotly_config,
            )

    with statistical_tab:
        correlation_chart = create_numeric_correlation_chart(dataframe)

        if correlation_chart is None:
            st.info("Au moins deux variables numeriques sont necessaires pour calculer les correlations.")
        else:
            st.plotly_chart(correlation_chart, use_container_width=True, config=plotly_config)

        numeric_dataframe = dataframe.select_dtypes(include="number")

        if not numeric_dataframe.empty:
            st.markdown("### Statistiques descriptives")
            statistics = (
                numeric_dataframe.describe()
                .transpose()
                .reset_index()
                .rename(
                    columns={
                        "index": "variable",
                        "count": "nombre",
                        "mean": "moyenne",
                        "std": "ecart_type",
                        "min": "minimum",
                        "25%": "quartile_25",
                        "50%": "mediane",
                        "75%": "quartile_75",
                        "max": "maximum",
                    }
                )
            )

            st.dataframe(statistics, use_container_width=True, hide_index=True)
