"""Modèle central : une ligne par FT et par prototype, avec la partie Étude, la partie Fabrication et l'impact qui les relie.

Les classeurs Follow-up portent déjà les deux parties sur la même ligne FT (feuille FT_Impact / FT_Impact_Global) :
- Étude      : statut DMU, statut FT, avancement des DAP, CID ;
- Fabrication: statut de réception, besoin vs réception, étape de montage, fournisseur, Plan B ;
- Impact     : conséquence sur le véhicule (colonne `consequence`) et situation qui en découle.
"""
import datetime as dt
import re
import pandas as pd
from src.classification import norm, normalize_status

FT_SHEETS = {"ft_impact", "ft_impact_global"}
BAD = {"KO", "EN RETARD", "MANQUANT", "A RISQUE"}
CLOSED = {"OK", "TERMINE", "ANNULE"}
NR = "NON RENSEIGNE"
CRITICAL_STEPS = ("structure", "body assembly", "mecanical", "mechanical", "electrical wiring", "dashboard", "roof", "harness")
POINTS = {"KO": 40, "EN RETARD": 35, "MANQUANT": 30, "A RISQUE": 25, "EN COURS": 8}
SIT_BOTH = "ETUDE ET FABRICATION EN DIFFICULTE"
SIT_STUDY = "ETUDE EN RISQUE -> FABRICATION EXPOSEE"
SIT_FAB = "RISQUE FABRICATION SEUL"
SIT_OK = "MAITRISE"
SIT_NONE = "NON SUIVI (AUCUN STATUT)"
SEVERITY_BONUS = {"BLOQUANT": 20, "MODERE": 8}
EMPTY_TEXT = {"", "nan", "none", "<na>", "-", "x", "tbc"}


def risk_label(score: float) -> str:
    return "CRITIQUE" if score >= 61 else "ELEVE" if score >= 41 else "MODERE" if score >= 21 else "FAIBLE"


def ft_key(value):
    """Clé de jointure FT : '061321', 61321 et '61321.0' donnent '61321'."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)) and float(value).is_integer():
        text = str(int(value))
    else:
        text = str(value).strip().upper()
    if not text or text in {"NAN", "NONE", "<NA>"}:
        return None
    return (text.lstrip("0") or "0") if text.isdigit() else text


def _val(row, names):
    for name in names:
        v = row.get(name)
        if v is None:
            continue
        try:
            if pd.isna(v):
                continue
        except (TypeError, ValueError):
            pass
        if isinstance(v, str) and v.strip().lower() in EMPTY_TEXT:
            continue
        return v
    return None


def _num(v):
    try:
        f = float(v)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def _date(v):
    if isinstance(v, (dt.datetime, pd.Timestamp)):
        d = v.date()
    elif isinstance(v, dt.date):
        d = v
    else:
        return None
    return d if d.year >= 2000 else None  # 1899-12-30 = zéro Excel


def _weeks(v):
    return [(2000 + int(y), int(w)) for y, w in re.findall(r"(?:20)?(\d{2})\s*W\s*(\d{1,2})", str(v).upper())]


def _text(v):
    return None if v is None else str(v).strip()


def _worst(statuses):
    order = ["KO", "EN RETARD", "MANQUANT", "A RISQUE", "EN COURS", "NON RENSEIGNE", "OK", "TERMINE", "ANNULE"]
    present = [s for s in statuses if s in order]
    return min(present, key=order.index) if present else NR


def study_status(dmu, ft_status, dap_late):
    if dmu == "KO": return "KO"
    if dap_late: return "EN RETARD"
    if dmu == "A RISQUE": return "A RISQUE"
    if "EN COURS" in (dmu, ft_status): return "EN COURS"
    if ft_status == "TERMINE": return "TERMINE"
    if dmu in {"OK", "TERMINE"}: return "OK"
    return NR


def severity(consequence):
    c = (consequence or "").lower()
    if "prevent" in c: return "BLOQUANT"
    if "unplanned" in c or "debug" in c: return "MODERE"
    if "no technical" in c or "no impact" in c: return "FAIBLE"
    return "NON PRECISE"


def _enrichment(loaded):
    suppliers, cids = {}, {}
    for sh in loaded:
        name, df = norm(sh["sheet_name"]), sh["dataframe"]
        proto = df["prototype"].iloc[0] if "prototype" in df.columns and len(df) else None
        if name.startswith("supplier_list") and "ft" in df.columns:
            for r in df.to_dict("records"):
                k = ft_key(r.get("ft"))
                if k:
                    suppliers[(proto, k)] = {"fournisseur": _text(_val(r, ["supplier_name"])), "plan_action": _text(_val(r, ["action_plan"]))}
        if name == "cid_stato_n" and "ft" in df.columns:
            for r in df.to_dict("records"):
                k = ft_key(r.get("ft"))
                if not k:
                    continue
                c = cids.setdefault((proto, k), {"n": 0, "st": [], "cout": 0.0, "crit": False})
                c["n"] += 1
                c["st"].append(normalize_status(_val(r, ["final_status", "check_dmu"])))
                c["cout"] += _num(r.get("cout_reel")) or 0.0
                c["crit"] = c["crit"] or str(r.get("critical_path")).strip().lower() == "yes"
    return suppliers, cids


def _model_row(r, proto, today, suppliers, cids):
    key = ft_key(r.get("ft"))
    dmu = normalize_status(_val(r, ["statut_dmu"]))
    ftst = normalize_status(_val(r, ["statut_ft"]))
    fab = normalize_status(_val(r, ["statut_impact"]))
    f = _num(_val(r, ["dap_volume_forecast", "nb_dap_prevue_sur_la_ft"]))
    s = _num(_val(r, ["dap_volume_sent"]))
    if f and s is None and "dap_volume_sent" in r:  # colonne présente mais vide = aucun DAP envoyé
        s = 0.0
    planned = _weeks(_val(r, ["date_dap_prevue", "dap_target_submission_date_from_dpt_file_week", "all_dap_with_target_date"]) or "")
    dap_late = bool(f and s is not None and s < f and planned and max(planned) < tuple(today.isocalendar()[:2]))
    cid = cids.get((proto, key))
    etude = study_status(dmu, ftst, dap_late)
    step = _text(_val(r, ["etape_fabrication", "steps"]))
    need = _date(_val(r, ["need_for_the_parts", "needs_for_parts"]))
    recv = _date(_val(r, ["date_reception_prevue"]))
    gap = (recv - need).days if need and recv else None
    plan_b = _text(_val(r, ["plan_b"]))
    conseq = _text(_val(r, ["consequence"]))
    sev = severity(conseq)
    sup = suppliers.get((proto, key), {})
    e_bad, f_bad = etude in BAD, fab in BAD
    e_pts, f_pts = POINTS.get(etude, 0), POINTS.get(fab, 0)
    if f_bad:
        if step and any(k in step.lower() for k in CRITICAL_STEPS): f_pts += 10
        if plan_b and "valid" in plan_b.lower(): f_pts = max(f_pts - 10, 0)
        elif not plan_b: f_pts += 10
        if gap is not None and gap > 30: f_pts += 10
    urgent = bool(need and (need - today).days <= 28 and (e_bad or f_bad))
    score = max(e_pts, f_pts) + (min(e_pts, f_pts) // 2 if e_bad and f_bad else 0)
    if e_bad or f_bad:
        score += SEVERITY_BONUS.get(sev, 0) + (10 if urgent else 0)
    score = min(score, 100)
    if e_bad and f_bad: sit = SIT_BOTH
    elif e_bad: sit = SIT_STUDY
    elif f_bad: sit = SIT_FAB
    elif etude == NR and fab == NR: sit = SIT_NONE
    else: sit = SIT_OK
    where = f" (DMU {_text(_val(r, ['statut_dmu'])) or '-'}, DAP {int(s) if s is not None else '?'}/{int(f) if f is not None else '?'})"
    if sit == SIT_STUDY:
        text = f"Étude {etude}{where} : la fabrication de l'étape « {step or 'non renseignée'} » dépend de cette FT, l'approvisionnement et le montage sont exposés."
    elif sit == SIT_BOTH:
        text = f"Étude {etude}{where} et fabrication {fab}" + (f" ({gap} j d'écart réception/besoin)" if gap and gap > 0 else "") + f" : double exposition sur l'étape « {step or 'non renseignée'} »."
    elif sit == SIT_FAB:
        text = f"Étude non bloquante (statut {etude}) mais fabrication {fab}" + (f" ({gap} j d'écart réception/besoin)" if gap and gap > 0 else "") + ": cause côté fournisseur, réception ou planning."
    elif sit == SIT_NONE:
        text = "Aucun statut étude ni fabrication renseigné pour cette FT : impact non évaluable."
    else:
        text = "Aucun blocage détecté sur cette FT."
    if conseq and (e_bad or f_bad): text += f" Conséquence véhicule : {conseq}."
    action = ("Escalader : sécuriser le Plan B et confirmer le responsable." if score >= 61 else
              "Traiter la cause et confirmer la date." if score >= 41 else
              "Compléter les statuts de cette FT." if sit == SIT_NONE else "Surveiller et mettre à jour les dates.")
    return {
        "prototype": proto, "ft": key, "description": _text(_val(r, ["description", "description_fr"])),
        "departement": _text(_val(r, ["departement"])), "domaine_systeme": _text(_val(r, ["domaine_systeme"])), "systeme": _text(_val(r, ["systeme"])),
        "criticite": _text(_val(r, ["criticity"])), "responsable": _text(_val(r, ["ft_responsible", "dap_responsible", "responsable"])),
        "etude_statut": etude, "etude_dmu": _text(_val(r, ["statut_dmu"])), "etude_statut_ft": _text(_val(r, ["statut_ft"])),
        "dap_prevus": f, "dap_envoyes": s, "dap_avancement_pct": round(100 * s / f) if f and s is not None else None,
        "dap_semaines": _text(_val(r, ["date_dap_prevue", "dap_target_submission_date_from_dpt_file_week"])), "dap_en_retard": dap_late,
        "cid_nb": cid["n"] if cid else 0, "cid_statut": _worst(cid["st"]) if cid else None, "cid_cout_eur": round(cid["cout"]) if cid and cid["cout"] else None,
        "cid_chemin_critique": bool(cid and cid["crit"]),
        "fab_statut": fab, "fab_etape": step, "fab_besoin_pieces": need, "fab_reception_prevue": recv, "fab_ecart_jours": gap,
        "fab_fournisseur": sup.get("fournisseur") or _text(_val(r, ["supplier_name", "late_part_supplier_name"])),
        "fab_delai_fournisseur_sem": _num(_val(r, ["supplier_delays", "supplier_lead_time"])), "fab_plan_b": plan_b, "fab_plan_action": sup.get("plan_action") or _text(_val(r, ["action_plan"])),
        "consequence_vehicule": conseq, "gravite_consequence": sev, "urgent": urgent,
        "situation": sit, "impact_consequence": text, "score_risque": score, "niveau_risque": risk_label(score), "action_recommandee": action,
        "couverture": "Complet" if etude != NR and fab != NR else "Étude seule" if etude != NR else "Fabrication seule" if fab != NR else "Aucun statut",
        "fichier_source": r.get("fichier_source"),
    }


def build_ft_table(loaded, today=None) -> pd.DataFrame:
    """Une ligne par (prototype, FT) du périmètre du prototype, avec Étude + Fabrication + Impact."""
    today = today or dt.date.today()
    suppliers, cids = _enrichment(loaded)
    rows = []
    for sh in loaded:
        if norm(sh["sheet_name"]) not in FT_SHEETS:
            continue
        df = sh["dataframe"]
        if "type" in df.columns:
            df = df[df["type"].astype(str).str.strip().str.upper().eq("FT")]
        if "proto_impact" in df.columns:  # périmètre : FT marquées 'X' pour ce prototype (les 'NA to Pn' sont hors périmètre)
            df = df[df["proto_impact"].astype(str).str.strip().str.upper().eq("X")]
        for r in df.to_dict("records"):
            if ft_key(r.get("ft")):
                rows.append(_model_row(r, r.get("prototype"), today, suppliers, cids))
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows).sort_values("score_risque", ascending=False)
    counts = out.groupby(["prototype", "ft"]).size().rename("nb_lignes_source")
    out = out.drop_duplicates(["prototype", "ft"], keep="first").join(counts, on=["prototype", "ft"])
    return out.reset_index(drop=True)


def proto_summary(ft: pd.DataFrame) -> pd.DataFrame:
    if ft.empty:
        return pd.DataFrame()
    rows = []
    for proto, g in ft.groupby("prototype"):
        f, s = g["dap_prevus"].sum(), g["dap_envoyes"].sum()
        rows.append({
            "prototype": proto, "ft_suivies": len(g),
            "etude_a_risque": int(g["etude_statut"].isin(BAD).sum()), "fab_a_risque": int(g["fab_statut"].isin(BAD).sum()),
            "etude_expose_fab": int(g["situation"].isin([SIT_STUDY, SIT_BOTH]).sum()), "critiques": int(g["niveau_risque"].eq("CRITIQUE").sum()),
            "eleves": int(g["niveau_risque"].eq("ELEVE").sum()), "score_max": int(g["score_risque"].max()),
            "avancement_dap_pct": round(100 * s / f) if f else None,
            "couverture_statuts_pct": round(100 * g["couverture"].eq("Complet").mean()),
        })
    return pd.DataFrame(rows).sort_values("score_max", ascending=False, ignore_index=True)


def planning_table(loaded) -> pd.DataFrame:
    """MASTER R01_Concac_Proto : PLAN vs SENT par département et par semaine, cumulés."""
    frames = [sh["dataframe"] for sh in loaded if norm(sh["sheet_name"]) == "r01_concac_proto"]
    if not frames:
        return pd.DataFrame()
    d = pd.concat(frames, ignore_index=True)
    need = {"departement", "category", "year", "week", "unit"}
    if not need.issubset(d.columns):
        return pd.DataFrame()
    d = d.assign(year=pd.to_numeric(d["year"], errors="coerce"), week=pd.to_numeric(d["week"], errors="coerce"), unit=pd.to_numeric(d["unit"], errors="coerce"))
    d = d.dropna(subset=["year", "week", "unit"])
    d["category"] = d["category"].astype(str).str.upper().str.strip()
    d["periode"] = d["year"].astype(int).astype(str) + "-S" + d["week"].astype(int).astype(str).str.zfill(2)
    g = d.groupby(["departement", "category", "periode"], dropna=False)["unit"].sum().reset_index().sort_values("periode")
    g["cumul"] = g.groupby(["departement", "category"])["unit"].cumsum()
    return g


def data_warnings(loaded, ft: pd.DataFrame) -> list:
    """Alertes de fiabilité des fichiers : prototypes identiques, feuille FT sans colonnes de statut, FT hors périmètre."""
    warns, sigs = [], {}
    for sh in loaded:
        if norm(sh["sheet_name"]) not in FT_SHEETS:
            continue
        df, proto = sh["dataframe"], sh["dataframe"]["prototype"].iloc[0]
        content = df.drop(columns=[c for c in ("prototype", "fichier_source", "cle_metier", "ligne_source") if c in df.columns])
        sig = int(pd.util.hash_pandas_object(content.astype(str), index=False).sum())
        sigs.setdefault(sig, []).append(proto)
        if not {"statut_dmu", "statut_ft", "statut_impact"} & set(df.columns):
            warns.append(f"{proto} : la feuille FT n'a aucune colonne de statut (DMU, FT, impact). Seule la liste des FT est disponible, l'impact ne peut pas être évalué.")
        elif "proto_impact" not in df.columns:
            warns.append(f"{proto} : pas de colonne proto_impact, toutes les FT sont prises sans filtrage de périmètre.")
    for protos in sigs.values():
        if len(protos) > 1:
            warns.append(f"{' et '.join(map(str, protos))} : feuilles FT strictement identiques. Vérifier qu'il ne s'agit pas d'une copie du même fichier.")
    for proto, g in (ft.groupby("prototype") if not ft.empty else []):
        if g["couverture"].eq("Aucun statut").mean() > 0.5:
            warns.append(f"{proto} : {g['couverture'].eq('Aucun statut').mean():.0%} des FT n'ont aucun statut, les risques affichés sont sous-estimés.")
        elif g["fab_statut"].eq(NR).mean() > 0.5:
            warns.append(f"{proto} : {g['fab_statut'].eq(NR).mean():.0%} des FT sans statut fabrication (pas de statut_impact), la partie fabrication n'est pas évaluable.")
        elif g["etude_statut"].eq(NR).mean() > 0.5:
            warns.append(f"{proto} : {g['etude_statut'].eq(NR).mean():.0%} des FT sans statut étude (DMU / FT).")
    return warns
