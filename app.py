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

def load_data_safe(sheet_name):
    try:
        data = conn.read(worksheet=sheet_name, ttl=0)
        # On nettoie les noms de colonnes
        data.columns = [str(c).lower().strip() for c in data.columns]
        return data
    except Exception as e:
        # Si la feuille est vide ou introuvable, on renvoie un tableau vide avec les bonnes colonnes
        st.warning(f"Note : La feuille '{sheet_name}' semble vide ou inaccessible.")
        return pd.DataFrame()

# Chargement individuel
df_inv = load_data_safe("Inventaire")
df_ventes = load_data_safe("Ventes")
df_clients = load_data_safe("Clients")
df_depenses = load_data_safe("Depenses")
df_devis = load_data_safe("Devis")


# Chargement initial des DataFrames
try:
    df_inv = load_data("Inventaire")
    df_ventes = load_data("Ventes")
    df_clients = load_data("Clients")
    df_depenses = load_data("Depenses")
    df_devis = load_data("Devis")
except Exception as e:
    st.error("Erreur de connexion au Google Sheets. Vérifiez vos Secrets et les noms d'onglets.")
    st.stop()


# --- FONCTIONS PDF (Format Euros pour éviter erreur symbole) ---
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
    pdf.cell(50, 15, f"{vente_data['prix_vente_final']} Euros", 1, 1, 'C')
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 10, "Merci pour votre achat chez Les Brocs de Charlotte !", align='C')
    output = pdf.output(dest='S')
    return bytes(output) if not isinstance(output, str) else output.encode('latin-1')


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
    pdf.cell(100, 6, "29610 GARLAN", ln=True)
    pdf.cell(100, 6, "lesbrocsdecharlotte@gmail.com")
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Devis N° DEV-{devis_data['id_devis']}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 6, f"Date : {devis_data['date_devis']}", ln=True)
    pdf.ln(5)
    pdf.set_fill_color(240, 230, 220)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(15, 10, "Qte", 1, 0, 'C', True)
    pdf.cell(125, 10, "Designation", 1, 0, 'L', True)
    pdf.cell(50, 10, "Total HT", 1, 1, 'C', True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(15, 20, "1", 1)
    pdf.multi_cell(125, 10, f"{devis_data['nom_projet']}\n{devis_data['details']}", 1)
    pdf.set_xy(150, pdf.get_y() - 20)
    pdf.cell(50, 20, f"{devis_data['montant']} Euros", 1, 1, 'C')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(140, 10, "TOTAL TTC (TVA non applicable art. 293B du CGI)", 0, 0, 'R')
    pdf.cell(50, 10, f"{devis_data['montant']} Euros", 1, 1, 'C')
    # Page CGV (Simplifiée pour le code)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Conditions Generales de Vente", ln=True, align='C')
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 5,
                   "1. Nature des produits: Meubles anciens...\n2. Prix: Hors TVA art 293B...\n3. Retours: Non acceptes.")
    output = pdf.output(dest='S')
    return bytes(output) if not isinstance(output, str) else output.encode('latin-1')


# --- INTERFACE ---
tabs = st.tabs(["📊 Dashboard", "📦 Atelier & Stock", "💰 Ventes", "📝 Devis", "👥 Clients", "💸 Dépenses"])

# 1. DASHBOARD
with tabs[0]:
    st.header("Analyses et Remuneration")
    if not df_ventes.empty:
        df_ventes['date_vente'] = pd.to_datetime(df_ventes['date_vente'])
        an_sel = st.selectbox("Annee", sorted(df_ventes['date_vente'].dt.year.unique(), reverse=True))

        ca_mensuel = df_ventes[df_ventes['date_vente'].dt.year == an_sel]['prix_vente_final'].sum()
        m_n_v = df_ventes[df_ventes['date_vente'].dt.year == an_sel]['marge_nette'].sum()

        # Calcul URSSAF (Différence entre marge brute théorique et marge nette stockée)
        # On peut aussi le recalculer directement : CA * 0.123 si activé
        urssaf_m = ca_mensuel * 0.123  # Estimation simplifiée pour le dashboard

        k1, k2, k3 = st.columns(3)
        k1.metric("CA Annuel", f"{ca_mensuel:.2f} Euros")
        k2.metric("Cout URSSAF (Est.)", f"{urssaf_m:.2f} Euros")
        k3.metric("Marge Nette", f"{m_n_v:.2f} Euros")

# --- 2. ATELIER & STOCK (VERSION GOOGLE SHEETS) ---
with tabs[1]:
    st.header("📦 Suivi du Stock et Prestations")
    
    with st.expander("➕ Ajouter un nouveau projet"):
        with st.form("new_meuble_form"):
            col1, col2 = st.columns(2)
            n_m = col1.text_input("Nom du meuble / Projet")
            type_p = col1.selectbox("Type de projet", ["Achat/Revente", "Prestation Client"])
            cat_m = col1.selectbox("Catégorie", ["Commode", "Table", "Assise", "Armoire", "Bureau", "Déco", "Autre"])
            d_entree = col1.date_input("Date d'entrée", value=date.today())
            
            p_achat = col2.number_input("Coût d'achat (€) - 0 si prestation", min_value=0.0)
            
            if st.form_submit_button("Enregistrer dans le Cloud"):
                if n_m:
                    # Préparation de la nouvelle ligne
                    new_data = {
                        "id": len(df_inv) + 1,
                        "nom": n_m,
                        "categorie": cat_m,
                        "statut": "À rénover",
                        "cout_total": float(p_achat),
                        "date_entree": str(d_entree),
                        "temps_passe": 0.0,
                        "cout_materiaux": 0.0,
                        "type_projet": type_p
                    }
                    
                    # Ajout au DataFrame existant
                    df_inv = pd.concat([df_inv, pd.DataFrame([new_data])], ignore_index=True)
                    
                    # Mise à jour du Google Sheets
                    conn.update(worksheet="Inventaire", data=df_inv)
                    st.success(f"✅ '{n_m}' a bien été ajouté à votre Google Sheets !")
                    st.rerun()

    st.divider()
    
    # Affichage du stock actuel
    if not df_inv.empty:
        # Nettoyage rapide pour l'affichage
        df_display = df_inv.copy()
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Le stock est vide. Utilisez le formulaire ci-dessus pour ajouter votre premier meuble.")

# 3. VENTES
with tabs[2]:
    st.header("💰 Ventes")
    with st.form("vente_form"):
        meuble_v = st.selectbox("Meuble", df_inv[df_inv['statut'] != 'Vendu']['nom'].tolist())
        client_v = st.selectbox("Client", df_clients['nom_client'].tolist())
        prix_v = st.number_input("Prix final", min_value=0.0)
        urs = st.checkbox("Urssaf (12.3%)", value=True)
        if st.form_submit_button("Vendre"):
            # Calcul marge
            row_m = df_inv[df_inv['nom'] == meuble_v].iloc[0]
            taxe = (prix_v * 0.123) if urs else 0
            m_n = prix_v - row_m['cout_total'] - row_m['cout_materiaux'] - taxe

            # Update Ventes
            new_v = pd.DataFrame([{"id_vente": len(df_ventes) + 1, "nom_meuble": meuble_v, "prix_vente_final": prix_v,
                                   "date_vente": str(date.today()), "marge_nette": m_n}])
            df_v_up = pd.concat([df_ventes, new_v], ignore_index=True)
            conn.update(worksheet="Ventes", data=df_v_up)

            # Update Stock
            df_inv.loc[df_inv['nom'] == meuble_v, 'statut'] = 'Vendu'
            conn.update(worksheet="Inventaire", data=df_inv)
            st.success("Vendu !")
            st.rerun()
