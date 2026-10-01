import datetime as dt
import io
import time
import zipfile
import streamlit as st
from components import views
from components.filters import apply_filters
from components.theme import inject_css, table
from src.excel_loader import load_excel_files
from src.ft_model import build_ft_table, data_warnings, planning_table, proto_summary

st.set_page_config(page_title="IVECO Protos Intelligence", page_icon="📊", layout="wide")
inject_css()
st.markdown('<div class="hero"><h1>IVECO Protos Intelligence</h1><p>Pour chaque prototype : la partie Étude, la partie Fabrication, et l\'impact de l\'une sur l\'autre.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("Mode d'emploi")
    st.markdown("1. Importer MASTER_SUIVI_PROTO et les Follow-up P1 à PN\n2. Lire la synthèse, puis un prototype\n3. Filtrer par département ou niveau de risque\n4. Exporter pour Power BI")
    if st.button("Vider le cache", width="stretch"):
        st.cache_data.clear()


@st.cache_data(show_spinner=False)
def process(payloads, today):
    loaded, errors = load_excel_files(payloads)
    ft = build_ft_table(loaded, today)
    return loaded, errors, ft, planning_table(loaded), data_warnings(loaded, ft)


uploads = st.file_uploader("Importer MASTER_SUIVI_PROTO et Follow-up_P1 à Follow-up_PN", type=["xlsx", "xlsm"], accept_multiple_files=True)
if not uploads:
    st.info("Importez les classeurs Excel pour lancer l'analyse.")
    st.stop()
start = time.perf_counter()
with st.spinner("Lecture des feuilles FT, calcul des impacts..."):
    loaded, errors, ft_all, plan, warnings = process([{"name": f.name, "content": f.getvalue()} for f in uploads], dt.date.today())
if errors:
    with st.expander(f"{len(errors)} fichier(s) ou feuille(s) non exploitable(s)"):
        st.write(errors)
if ft_all.empty:
    st.error("Aucune FT exploitable : il faut au moins un Follow-up avec une feuille FT_Impact.")
    st.stop()
st.success(f"{len(uploads)} fichier(s), {len(loaded)} feuille(s) métier, {len(ft_all):,} FT en {time.perf_counter()-start:.1f} s")

ft = apply_filters(ft_all)
summary = proto_summary(ft)
tabs = st.tabs(["Synthèse", "Par prototype", "Impact et conséquences", "Étude", "Fabrication", "Planning MASTER", "Qualité des données", "Données et export"])
with tabs[0]: views.overview(ft, summary, warnings)
with tabs[1]: views.prototype_view(ft)
with tabs[2]: views.impact_view(ft)
with tabs[3]: views.etude_view(ft)
with tabs[4]: views.fabrication_view(ft)
with tabs[5]: views.planning_view(plan)
with tabs[6]: views.quality_view(ft_all, warnings)
with tabs[7]:
    table(ft, height=560)
    import pandas as pd
    exports = {"ft_consolidees.csv": ft, "synthese_prototypes.csv": summary, "impact_consequences.csv": ft[ft["score_risque"] >= 21], "planning_master.csv": plan,
               "alertes_donnees.csv": pd.DataFrame({"alerte": warnings})}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, frame in exports.items():
            z.writestr(name, frame.to_csv(index=False, sep=";", encoding="utf-8-sig"))
    st.download_button("Télécharger les exports Power BI (ZIP de 5 CSV)", buf.getvalue(), "iveco_protos_exports.zip", "application/zip", width="stretch")
