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

# 2. CONNEXION GOOGLE SHEETS SÉCURISÉE
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data_safe(sheet_name, default_columns):
    try:
        data = conn.read(worksheet=sheet_name, ttl=0)
        if data is None or data.empty:
            return pd.DataFrame(columns=default_columns)
        # Nettoyage des colonnes
        data.columns = [str(c).lower().strip() for c in data.columns]
        for col in default_columns:
            if col not in data.columns:
                data[col] = None
        return data
    except:
        return pd.DataFrame(columns=default_columns)

# Définition des structures
cols_inv = ["id", "nom", "categorie", "statut", "cout_total", "date_entree", "temps_passe", "cout_materiaux", "type_projet"]
cols_ventes = ["id_vente", "nom_meuble", "prix_vente_final", "date_vente", "marge_nette"]
cols_clients = ["id_client", "nom_client", "email", "telephone"]
cols_depenses = ["id_depense", "date", "categorie", "montant_ttc"]
cols_devis = ["id_devis", "nom_projet", "montant", "date_devis", "id_client", "details"]

# Chargement des données
df_inv = load_data_safe("Inventaire", cols_inv)
df_ventes = load_data_safe("Ventes", cols_ventes)
df_clients = load_data_safe("Clients", cols_clients)
df_depenses = load_data_safe("Depenses", cols_depenses)
df_devis = load_data_safe("Devis", cols_devis)

# --- FONCTIONS PDF ---
def generer_facture(vente_data, client_nom):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 20, "LES BROCS DE CHARLOTTE", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, f"Facture N° {vente_data['id_vente']}", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(100, 10, f"Date : {vente_data['date_vente']}")
    pdf.cell(100, 10, f"Client : {client_nom}", ln=True, align='R')
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(140, 10, "Designation", 1, 0, 'L', True)
    pdf.cell(50, 10, "Total TTC", 1, 1, 'C', True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(140, 15, f"{vente_data['nom_meuble']}", 1)
    pdf.cell(50, 15, f"{vente_data['prix_vente_final']} Euros", 1, 1, 'C')
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 10, "Merci pour votre achat !\nTVA non applicable - Art. 293B du CGI", align='C')
    return pdf.output(dest='S').encode('latin-1')

def generer_devis_pdf(devis_data, client_nom):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(139, 90, 60) 
    pdf.cell(0, 15, "LES BROCS DE CHARLOTTE", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(100, 6, "Les Brocs de Charlotte")
    pdf.cell(0, 6, client_nom, ln=True, align='R')
    pdf.cell(100, 6, "11, Rue du Bois de la Roche, 29610 GARLAN")
    pdf.ln(15)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Devis N° DEV-{devis_data['id_devis']}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 6, f"Date : {devis_data['date_devis']}", ln=True)
    pdf.ln(5)
    pdf.set_fill_color(240, 230, 220)
    pdf.cell(15, 10, "Qte", 1, 0, 'C', True)
    pdf.cell(125, 10, "Designation", 1, 0, 'L', True)
    pdf.cell(50, 10, "Total HT", 1, 1, 'C', True)
    pdf.cell(15, 20, "1", 1)
    pdf.multi_cell(125, 10, f"{devis_data['nom_projet']}\n{devis_data['details']}", 1)
    pdf.set_xy(150, pdf.get_y()-20)
    pdf.cell(50, 20, f"{devis_data['montant']} Euros", 1, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(140, 10, "TOTAL TTC (TVA non applicable)", 0, 0, 'R')
    pdf.cell(50, 10, f"{devis_data['montant']} Euros", 1, 1, 'C')
    # Page 2 : CGV
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Conditions Generales de Vente", ln=True, align='C')
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 5, "1. Objet: Les présentes conditions...\n2. Devis: Valable 30 jours...\n3. Paiement: 30% d'acompte...")
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE PRINCIPALE ---
st.title("🪑 Les Brocs de Charlotte")

tabs = st.tabs(["📊 Dashboard", "📦 Atelier & Stock", "💰 Ventes", "📝 Devis", "👥 Clients", "💸 Dépenses"])

# 1. DASHBOARD
with tabs[0]:
    st.header("Analyses et Rémunération")
    if not df_ventes.empty:
        df_ventes['date_vente'] = pd.to_datetime(df_ventes['date_vente'])
        annee = st.selectbox("Année", sorted(df_ventes['date_vente'].dt.year.unique(), reverse=True))
        
        df_annee = df_ventes[df_ventes['date_vente'].dt.year == annee]
        ca = df_annee['prix_vente_final'].sum()
        marge = df_annee['marge_nette'].sum()
        urssaf = ca * 0.123
        
        c1, c2, c3 = st.columns(3)
        c1.metric("CA Annuel", f"{ca:.2f} €")
        c2.metric("Cotisations URSSAF (12.3%)", f"{urssaf:.2f} €", delta_color="inverse")
        c3.metric("Rémunération Nette", f"{marge:.2f} €")
        
        fig = px.bar(df_annee, x='date_vente', y='prix_vente_final', title="Ventes dans le temps", color_discrete_sequence=['#8B5A3C'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune vente enregistrée pour le moment.")

# 2. ATELIER & STOCK
with tabs[1]:
    st.header("Gestion du Stock")
    with st.expander("➕ Ajouter un meuble"):
        with st.form("add_form"):
            n = st.text_input("Nom du meuble")
            cat = st.selectbox("Catégorie", ["Commode", "Table", "Assise", "Armoire", "Bureau", "Autre"])
            t_p = st.selectbox("Type", ["Achat/Revente", "Prestation Client"])
            c_a = st.number_input("Prix d'achat (€)", min_value=0.0)
            if st.form_submit_button("Ajouter au Stock"):
                new_m = pd.DataFrame([{"id": len(df_inv)+1, "nom": n, "categorie": cat, "statut": "À rénover", "cout_total": c_a, "date_entree": str(date.today()), "temps_passe": 0, "cout_materiaux": 0, "type_projet": t_p}])
                df_inv = pd.concat([df_inv, new_m], ignore_index=True)
                conn.update(worksheet="Inventaire", data=df_inv)
                st.success("Meuble ajouté !")
                st.rerun()
    
    # Edition rapide du stock
    st.subheader("Stock actuel")
    edited_df = st.data_editor(df_inv, num_rows="dynamic", use_container_width=True)
    if st.button("Sauvegarder les modifications du stock"):
        conn.update(worksheet="Inventaire", data=edited_df)
        st.success("Stock mis à jour !")

# 3. VENTES
with tabs[2]:
    st.header("Enregistrer une vente")
    meubles_dispos = df_inv[df_inv['statut'] != 'Vendu']['nom'].tolist()
    if meubles_dispos:
        with st.form("vente_form"):
            m_v = st.selectbox("Meuble vendu", meubles_dispos)
            c_v = st.selectbox("Client", df_clients['nom_client'].tolist() if not df_clients.empty else ["Client Passage"])
            p_v = st.number_input("Prix de vente final (€)", min_value=0.0)
            if st.form_submit_button("Valider la vente"):
                # Calcul marge
                meuble_row = df_inv[df_inv['nom'] == m_v].iloc[0]
                marge_n = p_v - meuble_row['cout_total'] - meuble_row['cout_materiaux'] - (p_v * 0.123)
                
                # Update Ventes
                new_v = pd.DataFrame([{"id_vente": len(df_ventes)+1, "nom_meuble": m_v, "prix_vente_final": p_v, "date_vente": str(date.today()), "marge_nette": marge_n}])
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                conn.update(worksheet="Ventes", data=df_ventes)
                
                # Update Stock
                df_inv.loc[df_inv['nom'] == m_v, 'statut'] = 'Vendu'
                conn.update(worksheet="Inventaire", data=df_inv)
                st.success("Vente enregistrée !")
                st.rerun()
    
    st.subheader("Historique des ventes")
    st.dataframe(df_ventes, use_container_width=True)

# 4. DEVIS
with tabs[3]:
    st.header("Éditeur de Devis")
    with st.form("devis_form"):
        d_nom = st.text_input("Nom du projet")
        d_client = st.selectbox("Client pour devis", df_clients['nom_client'].tolist() if not df_clients.empty else ["Nouveau"])
        d_montant = st.number_input("Montant total (€)", min_value=0.0)
        d_details = st.text_area("Détails de la prestation")
        if st.form_submit_button("Générer Devis"):
            new_d = {"id_devis": len(df_devis)+1, "nom_projet": d_nom, "montant": d_montant, "date_devis": str(date.today()), "details": d_details}
            pdf_file = generer_devis_pdf(new_d, d_client)
            st.download_button("📥 Télécharger le Devis PDF", pdf_file, f"Devis_{d_nom}.pdf", "application/pdf")
            # Sauvegarde optionnelle dans le Sheets
            df_devis = pd.concat([df_devis, pd.DataFrame([new_d])], ignore_index=True)
            conn.update(worksheet="Devis", data=df_devis)

# 5. CLIENTS
with tabs[4]:
    st.header("Répertoire Clients")
    with st.form("client_form"):
        c_n = st.text_input("Nom du client")
        c_e = st.text_input("Email")
        if st.form_submit_button("Ajouter Client"):
            new_c = pd.DataFrame([{"id_client": len(df_clients)+1, "nom_client": c_n, "email": c_e}])
            df_clients = pd.concat([df_clients, new_c], ignore_index=True)
            conn.update(worksheet="Clients", data=df_clients)
            st.rerun()
    st.dataframe(df_clients, use_container_width=True)

# 6. DÉPENSES
with tabs[5]:
    st.header("Dépenses (Consommables, Outils)")
    with st.form("dep_form"):
        d_d = st.date_input("Date")
        d_c = st.text_input("Objet / Catégorie")
        d_m = st.number_input("Montant (€)", min_value=0.0)
        if st.form_submit_button("Enregistrer Dépense"):
            new_dep = pd.DataFrame([{"id_depense": len(df_depenses)+1, "date": str(d_d), "categorie": d_c, "montant_ttc": d_m}])
            df_depenses = pd.concat([df_depenses, new_dep], ignore_index=True)
            conn.update(worksheet="Depenses", data=df_depenses)
            st.rerun()
    st.dataframe(df_depenses, use_container_width=True)
