import io
import time
import zipfile
import streamlit as st
from components.charts import display_detailed_charts
from components.dashboard import display_dashboard
from components.filters import apply_filters
from src.cleaning import clean_dataframe
from src.concatenation import concatenate_sheets, split_business_tables
from src.costs import calculate_cost_kpis, extract_costs
from src.excel_loader import load_excel_files
from src.impacts import build_impact_table
from src.validation import validate_dataframe

st.set_page_config(page_title="IVECO Protos Intelligence", page_icon="📊", layout="wide")
st.markdown("""<style>.stApp{background:#f3f6f8}.block-container{padding-top:1.5rem}[data-testid=stMetric]{background:white;border:1px solid #d8e2ea;border-radius:8px;padding:14px}.hero{background:white;border-left:6px solid #006f95;padding:18px 22px;margin-bottom:16px}.hero h1{color:#00334d;margin:0}.hero p{color:#64748b;margin:5px 0 0}</style>""", unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>IVECO Protos Intelligence</h1><p>Consolidation P1 à PN, séparation Étude / Fabrication, impacts, risques, coûts et export Power BI.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("Processus")
    st.markdown("1. Importer les fichiers\n2. Détecter les feuilles métier\n3. Séparer Étude/Fabrication\n4. Calculer les impacts\n5. Exporter")
    if st.button("Vider le cache", use_container_width=True): st.cache_data.clear()

@st.cache_data(show_spinner=False)
def process(payloads):
    loaded, errors = load_excel_files(payloads)
    all_data = clean_dataframe(concatenate_sheets(loaded))
    tables = split_business_tables(all_data)
    impacts = build_impact_table(all_data)
    costs = extract_costs(all_data)
    validation = validate_dataframe(all_data)
    return loaded, errors, all_data, tables, impacts, costs, validation, calculate_cost_kpis(costs)

uploads = st.file_uploader("Importer MASTER_SUIVI_PROTO et Follow-up_P1 à Follow-up_PN", type=["xlsx", "xlsm"], accept_multiple_files=True)
if not uploads:
    st.info("Importez les classeurs Excel pour lancer l'analyse."); st.stop()
payloads = [{"name": f.name, "content": f.getvalue()} for f in uploads]
start = time.perf_counter()
with st.spinner("Analyse des feuilles, classification et calcul des impacts..."):
    loaded, errors, data, tables, impacts, costs, validation, cost_kpis = process(payloads)
if errors:
    with st.expander(f"{len(errors)} feuille(s) non exploitable(s)"):
        st.write(errors)
if data.empty:
    st.error("Aucune donnée exploitable détectée."); st.stop()
st.success(f"{len(uploads)} fichier(s), {len(loaded)} feuille(s), {len(data):,} lignes en {time.perf_counter()-start:.1f} s")
filtered = apply_filters(data)
filtered_tables = split_business_tables(filtered)
filtered_ids = set(filtered.get("id_ligne", []))
filtered_impacts = impacts[impacts["id_ligne"].isin(filtered_ids)] if not impacts.empty else impacts
filtered_costs = costs[costs["id_ligne"].isin(filtered_ids)] if not costs.empty else costs
filtered_validation = validate_dataframe(filtered)
filtered_cost_kpis = calculate_cost_kpis(filtered_costs)

tabs = st.tabs(["Vue exécutive", "Étude", "Fabrication", "Impacts", "Coûts", "Qualité", "Données", "Export Power BI"])
with tabs[0]: display_dashboard(filtered, filtered_tables, filtered_impacts, filtered_validation, filtered_cost_kpis)
with tabs[1]:
    st.subheader("Partie Étude")
    st.caption("FT, DMU, CID, DAP, maturité, criticité, statuts et responsables.")
    st.dataframe(filtered_tables["etude"], use_container_width=True, height=650, hide_index=True)
with tabs[2]:
    st.subheader("Partie Fabrication")
    st.caption("EBOM, pièces, PR/RDA, commandes, fournisseurs, réceptions, build, Plan B et retrofit.")
    st.dataframe(filtered_tables["fabrication"], use_container_width=True, height=650, hide_index=True)
with tabs[3]:
    st.subheader("Impacts et conséquences")
    display_detailed_charts(filtered, filtered_impacts, filtered_costs)
    st.dataframe(filtered_impacts, use_container_width=True, height=650, hide_index=True)
with tabs[4]:
    st.subheader("Coûts")
    st.metric("Coût total détecté", f"{filtered_cost_kpis['total_cost']:,.2f}")
    st.dataframe(filtered_costs, use_container_width=True, height=600, hide_index=True)
with tabs[5]:
    st.subheader("Qualité DAP / CID / données")
    q = st.columns(5)
    q[0].metric("Lignes", filtered_validation["total_rows"]); q[1].metric("Doublons", filtered_validation["duplicate_rows"])
    q[2].metric("Cellules vides", filtered_validation["missing_cells"]); q[3].metric("Valeurs négatives", filtered_validation["negative_values"])
    q[4].metric("Score", f"{filtered_validation['quality_score']:.1f} %")
    st.dataframe(filtered_validation["issues"], use_container_width=True, hide_index=True)
with tabs[6]: st.dataframe(filtered, use_container_width=True, height=700, hide_index=True)
with tabs[7]:
    exports = {"donnees_consolidees.csv": filtered, "etude.csv": filtered_tables["etude"], "fabrication.csv": filtered_tables["fabrication"], "impacts_consequences.csv": filtered_impacts, "couts.csv": filtered_costs, "anomalies.csv": filtered_validation["issues"]}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for name, frame in exports.items(): z.writestr(name, frame.to_csv(index=False, sep=";", encoding="utf-8-sig"))
    st.download_button("Télécharger tous les exports Power BI", buffer.getvalue(), "iveco_protos_exports.zip", "application/zip", use_container_width=True)
