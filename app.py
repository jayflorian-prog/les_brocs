import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os
import plotly.express as px
from fpdf import FPDF
from datetime import date, datetime, timedelta
from PIL import Image

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Les Brocs de Charlotte", layout="wide", page_icon="🪑")

# 2. CONNEXION GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet_name):
    # Lecture directe depuis Google Sheets
    df = conn.read(worksheet=worksheet_name, ttl=0)
    if df is not None and not df.empty:
        # Nettoyage des colonnes pour correspondre au code
        df.columns = [str(c).lower().strip() for c in df.columns]
    return df

# Chargement des données au démarrage
df_inv_all = load_data("Inventaire")
df_v = load_data("Ventes")
df_cl = load_data("Clients")
df_dep_all = load_data("Depenses")
df_devis_all = load_data("Devis")

# --- FONCTIONS PDF (TES VERSIONS ORIGINALES) ---
def generer_facture(vente_data, client_nom):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 20, "LES BROCS DE CHARLOTTE", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, f"Facture N° {vente_data['id_vente']}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(100, 10, f"Date : {vente_data['date_vente']}")
    pdf.cell(100, 10, f"Client : {client_nom}", ln=True, align='R')
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, "Designation", 1, 0, 'L', True)
    pdf.cell(50, 10, "Total TTC", 1, 1, 'C', True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(140, 15, f"{vente_data['nom_meuble']}", 1)
    pdf.cell(50, 15, f"{float(vente_data['prix_vente_final']):.2f} Euros", 1, 1, 'C')
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 10, "Merci pour votre achat chez Les Brocs de Charlotte !", align='C')
    return pdf.output(dest='S').encode('latin-1')

def generer_devis_pdf(devis_data, client_nom):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(139, 90, 60)
    pdf.cell(0, 15, "LES BROCS DE CHARLOTTE", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 5, "Renovation de meubles & brocante en ligne", ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 6, "Les Brocs de Charlotte")
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 6, client_nom, ln=True, align='R')
    pdf.cell(100, 6, "11, Rue du Bois de la Roche")
    pdf.cell(0, 6, "29610 GARLAN", ln=True, align='R')
    pdf.ln(15)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Devis N° DEV-{devis_data['id_devis']}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 6, f"Date : {devis_data['date_devis']}", ln=True)
    pdf.ln(10)
    pdf.set_fill_color(240, 230, 220)
    pdf.cell(15, 10, "Qte", 1, 0, 'C', True)
    pdf.cell(125, 10, "Designation", 1, 0, 'L', True)
    pdf.cell(50, 10, "Total HT", 1, 1, 'C', True)
    pdf.cell(15, 20, "1", 1)
    pdf.multi_cell(125, 10, f"{devis_data['nom_projet']}\n{devis_data['details']}", 1)
    pdf.set_xy(150, pdf.get_y()-20)
    pdf.cell(50, 20, f"{float(devis_data['montant']):.2f} Euros", 1, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(140, 10, "TOTAL TTC (TVA non applicable)", 0, 0, 'R')
    pdf.cell(50, 10, f"{float(devis_data['montant']):.2f} Euros", 1, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE PRINCIPALE ---
st.title("🪑 Les Brocs de Charlotte")
tabs = st.tabs(["📊 Dashboard", "📦 Atelier & Stock", "💰 Ventes", "📝 Devis", "👥 Clients", "💸 Dépenses"])

# --- 1. DASHBOARD (TA LOGIQUE PC) ---
with tabs[0]:
    st.header("Analyses et Rémunération")
    if not df_v.empty:
        df_v['date_vente'] = pd.to_datetime(df_v['date_vente'])
        annees = sorted(df_v['date_vente'].dt.year.unique(), reverse=True)
        c1, c2 = st.columns(2)
        an_sel = c1.selectbox("Année", annees)
        liste_mois = {1:"Janvier", 2:"Février", 3:"Mars", 4:"Avril", 5:"Mai", 6:"Juin", 7:"Juillet", 8:"Août", 9:"Septembre", 10:"Octobre", 11:"Novembre", 12:"Décembre"}
        m_sel = c2.selectbox("Mois", list(liste_mois.keys()), format_func=lambda x: liste_mois[x], index=datetime.now().month-1)

        df_m = df_v[(df_v['date_vente'].dt.year == an_sel) & (df_v['date_vente'].dt.month == m_sel)]
        
        dep_m = 0
        if not df_dep_all.empty:
            df_dep_all['date'] = pd.to_datetime(df_dep_all['date'])
            dep_m = df_dep_all[(df_dep_all['date'].dt.year == an_sel) & (df_dep_all['date'].dt.month == m_sel)]['montant_ttc'].sum()

        ca_m = df_m['prix_vente_final'].sum()
        m_n_v = df_m['marge_nette'].sum()
        b_r = m_n_v - dep_m
        
        ids_v = df_m['id_meuble'].tolist()
        t_m = df_inv_all[df_inv_all['id'].isin(ids_v)]['temps_passe'].sum()

        st.write(f"### 📈 Résultats de {liste_mois[m_sel]} {an_sel}")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("CA Mensuel", f"{ca_m:,.2f} €")
        k2.metric("Marge Nette", f"{m_n_v:,.2f} €")
        k3.metric("Bénéfice Net Réel", f"{b_r:,.2f} €")

        st.divider()
        st.subheader("💰 Calculateur de Salaire")
        p_h = t_m * 25
        rel = b_r - p_h if b_r > p_h else 0
        bonus = rel * 0.60
        part_ent = rel * 0.40
        total_ch = p_h + bonus

        cs1, cs2 = st.columns(2)
        cs1.success(f"**Salaire Charlotte : {total_ch:,.2f} €** (Heures: {p_h:,.2f}€ + Bonus: {bonus:,.2f}€)")
        cs2.warning(f"**Part Entreprise (40%) : {part_ent:,.2f} €**")

        st.subheader(f"📊 Évolution du CA en {an_sel}")
        df_an = df_v[df_v['date_vente'].dt.year == an_sel].copy()
        df_an['mois'] = df_an['date_vente'].dt.month.map(liste_mois)
        fig = px.bar(df_an.groupby('mois')['prix_vente_final'].sum().reset_index(), x='mois', y='prix_vente_final', color_discrete_sequence=['#d4a373'])
        st.plotly_chart(fig, use_container_width=True)

# --- 2. ATELIER & STOCK (TES CONTAINERS) ---
with tabs[1]:
    st.header("📦 Suivi du Stock et Prestations")
    with st.expander("➕ Ajouter un nouveau projet"):
        with st.form("new_meuble_form"):
            col1, col2 = st.columns(2)
            n_m = col1.text_input("Nom du meuble")
            type_p = col1.selectbox("Type", ["Achat/Revente", "Prestation Client"])
            cat_m = col1.selectbox("Catégorie", ["Commode", "Table", "Assise", "Armoire", "Bureau", "Déco", "Autre"])
            d_ent = col1.date_input("Date d'entrée", value=date.today())
            p_achat = col2.number_input("Coût d'achat (€)", min_value=0.0)
            if st.form_submit_button("Enregistrer"):
                new_data = pd.DataFrame([{"id": len(df_inv_all)+1, "nom": n_m, "categorie": cat_m, "statut": "À rénover", "cout_total": p_achat, "date_entree": str(d_ent), "photo": "", "temps_passe": 0, "cout_materiaux": 0, "type_projet": type_p}])
                df_inv_all = pd.concat([df_inv_all, new_data], ignore_index=True)
                conn.update(worksheet="Inventaire", data=df_inv_all)
                st.rerun()

    st.divider()
    df_s = df_inv_all[df_inv_all['statut'] != 'Vendu'].sort_values('id', ascending=False)
    for _, row in df_s.iterrows():
        with st.container(border=True):
            ci, ce = st.columns([3, 2])
            with ci:
                st.subheader(row['nom'])
                st.write(f"🏷️ `{row['type_projet']}` | 🕒 {row['temps_passe']}h | 🎨 {row['cout_materiaux']}€")
                st.caption(f"Entré le {row['date_entree']}")
            with ce:
                new_st = st.selectbox("Statut", ["À rénover", "En cours", "Terminé"], index=0, key=f"s_{row['id']}")
                t_p = st.number_input("+ Heures", min_value=0.0, step=0.5, key=f"t_{row['id']}")
                m_p = st.number_input("+ Matériaux (€)", min_value=0.0, key=f"m_{row['id']}")
                if st.button("Mettre à jour", key=f"b_{row['id']}", use_container_width=True):
                    df_inv_all.loc[df_inv_all['id'] == row['id'], ['statut', 'temps_passe', 'cout_materiaux']] = [new_st, row['temps_passe']+t_p, row['cout_materiaux']+m_p]
                    conn.update(worksheet="Inventaire", data=df_inv_all)
                    st.rerun()

# --- 3. VENTES (TES LOGIQUES DE CALCUL) ---
with tabs[2]:
    st.header("💰 Ventes et Encaissements")
    df_dispo = df_inv_all[df_inv_all['statut'] != 'Vendu']
    colv1, colv2 = st.columns(2)
    with colv1:
        with st.form("form_vente"):
            m_sel = st.selectbox("Meuble", df_dispo['nom'].tolist() if not df_dispo.empty else ["Aucun"])
            cl_sel = st.selectbox("Client", df_cl['nom_client'].tolist() if not df_cl.empty else ["Passage"])
            p_v = st.number_input("Prix de vente TTC (€)", min_value=0.0)
            plat = st.selectbox("Canal", ["Instagram", "Facebook", "Leboncoin", "Boutique", "Direct"])
            if st.form_submit_button("Valider la vente"):
                row_m = df_dispo[df_dispo['nom'] == m_sel].iloc[0]
                m_n = p_v - row_m['cout_total'] - row_m['cout_materiaux'] - (p_v * 0.123)
                new_v = pd.DataFrame([{"id_vente": len(df_v)+1, "id_meuble": row_m['id'], "nom_meuble": m_sel, "prix_vente_final": p_v, "date_vente": str(date.today()), "id_client": 0, "plateforme": plat, "marge_nette": m_n}])
                df_v = pd.concat([df_v, new_v], ignore_index=True)
                df_inv_all.loc[df_inv_all['id'] == row_m['id'], 'statut'] = 'Vendu'
                conn.update(worksheet="Ventes", data=df_v)
                conn.update(worksheet="Inventaire", data=df_inv_all)
                st.rerun()

    st.subheader("Historique")
    st.dataframe(df_v, use_container_width=True)

# --- 4, 5, 6 : DEVIS, CLIENTS, DEPENSES (TES FORMULAIRES PC) ---
with tabs[3]:
    st.header("📝 Gestion des Devis")
    with st.form("devis_f"):
        d_n = st.text_input("Objet")
        d_m = st.number_input("Montant (€)")
        d_det = st.text_area("Détails")
        if st.form_submit_button("Créer Devis"):
            new_dev = pd.DataFrame([{"id_devis": len(df_devis_all)+1, "nom_projet": d_n, "montant": d_m, "date_devis": str(date.today()), "details": d_det}])
            df_devis_all = pd.concat([df_devis_all, new_dev], ignore_index=True)
            conn.update(worksheet="Devis", data=df_devis_all)
            st.rerun()
    for _, rd in df_devis_all.iterrows():
        st.download_button(f"📥 Devis {rd['nom_projet']}", data=generer_devis_pdf(rd, "Client"), file_name=f"Devis_{rd['id_devis']}.pdf")

with tabs[4]:
    st.header("👥 Base Clients")
    with st.form("cl_f"):
        nc = st.text_input("Nom Client")
        if st.form_submit_button("Ajouter"):
            df_cl = pd.concat([df_cl, pd.DataFrame([{"id_client": len(df_cl)+1, "nom_client": nc}])], ignore_index=True)
            conn.update(worksheet="Clients", data=df_cl)
            st.rerun()
    st.dataframe(df_cl, use_container_width=True)

with tabs[5]:
    st.header("💸 Dépenses")
    with st.form("dep_f"):
        dm = st.number_input("Montant (€)")
        dc = st.text_input("Objet")
        if st.form_submit_button("Enregistrer"):
            df_dep_all = pd.concat([df_dep_all, pd.DataFrame([{"id_depense": len(df_dep_all)+1, "date": str(date.today()), "categorie": dc, "montant_ttc": dm}])], ignore_index=True)
            conn.update(worksheet="Depenses", data=df_dep_all)
            st.rerun()
    st.dataframe(df_dep_all, use_container_width=True)
