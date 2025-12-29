#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Veille V3 - Dashboard Streamlit (Version améliorée)
=======================================================

Interface web pour visualiser et gérer la veille technologique.
Partage la même base de données SQLite que le serveur MCP.

Fonctionnalités :
- Affichage des favoris avec filtres et recherche
- Historique des recherches avec indication des rapports associés
- Visualisation des rapports avec ajout aux favoris
- Statistiques d'utilisation

Lancement :
    streamlit run dashboard.py
"""

import streamlit as st
import sqlite3
import json
import re
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_DIR = Path(__file__).parent.parent
DB_PATH = PROJECT_DIR / "data" / "veille.db"

st.set_page_config(
    page_title="MCP Veille V3",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# THÉMATIQUES (pour affichage sur le dashboard)
# =============================================================================

THEMATIQUES = {
    "Claude & Anthropic": {
        "description": "Actualités Anthropic, Claude AI, protocole MCP",
        "categorie": "IA"
    },
    "Écosystème LLM": {
        "description": "OpenAI, Google Gemini, Mistral, Meta Llama et autres grands modèles",
        "categorie": "IA"
    },
    "IA Europe & Réglementation": {
        "description": "AI Act, RGPD appliqué à l'IA, positions CNIL",
        "categorie": "IA"
    },
    "HR Tech & Formation": {
        "description": "Cornerstone, LMS, talent management, formation professionnelle",
        "categorie": "PRO"
    },
    "Agents IA & Automatisation": {
        "description": "AI Agents, RAG, LangChain, automatisation intelligente",
        "categorie": "PRO"
    },
    "Open Source & Outils Dev": {
        "description": "Hugging Face, Open WebUI, Ollama, outils développeurs IA",
        "categorie": "PRO"
    }
}

# =============================================================================
# FONCTIONS BASE DE DONNÉES
# =============================================================================

def get_db_connection():
    """Crée une connexion à la base de données."""
    if not DB_PATH.exists():
        st.error(f"Base de données non trouvée: {DB_PATH}")
        st.info("Lancez d'abord une commande via Claude Desktop pour initialiser la base.")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_favoris(limite: int = 50, search: str = None) -> list:
    """Récupère les favoris depuis la base de données."""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        if search:
            cursor.execute("""
                SELECT * FROM favoris 
                WHERE titre LIKE ? OR description LIKE ? OR tags LIKE ?
                ORDER BY date_ajout DESC LIMIT ?
            """, (f"%{search}%", f"%{search}%", f"%{search}%", limite))
        else:
            cursor.execute("""
                SELECT * FROM favoris ORDER BY date_ajout DESC LIMIT ?
            """, (limite,))
        
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        st.error(f"Erreur lecture favoris: {e}")
        return []
    finally:
        conn.close()


def ajouter_favori(url: str, titre: str, source: str = "", description: str = "", 
                   date_article: str = "", tags: str = "", thematique: str = "") -> dict:
    """Ajoute un article aux favoris."""
    conn = get_db_connection()
    if not conn:
        return {"success": False, "error": "Connexion BD impossible"}
    
    try:
        cursor = conn.cursor()
        
        # Vérifier si déjà existant
        cursor.execute("SELECT id FROM favoris WHERE url = ?", (url,))
        if cursor.fetchone():
            return {"success": False, "error": "Article déjà dans les favoris"}
        
        cursor.execute("""
            INSERT INTO favoris (url, titre, source, description, date_article, date_ajout, tags, thematique)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (url, titre, source, description, date_article, datetime.now().isoformat(), tags, thematique))
        
        conn.commit()
        return {"success": True, "message": "Favori ajouté", "favori_id": cursor.lastrowid}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def est_en_favori(url: str) -> bool:
    """Vérifie si un article (par son URL) est déjà dans les favoris."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM favoris WHERE url = ?", (url,))
        return cursor.fetchone() is not None
    except Exception:
        return False
    finally:
        conn.close()


def get_favoris_urls() -> set:
    """Récupère l'ensemble des URLs des favoris pour vérification rapide."""
    conn = get_db_connection()
    if not conn:
        return set()
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT url FROM favoris")
        return {row[0] for row in cursor.fetchall()}
    except Exception:
        return set()
    finally:
        conn.close()


def exporter_favoris_markdown() -> str:
    """Exporte tous les favoris au format Markdown."""
    favoris = get_favoris(limite=1000)
    
    if not favoris:
        return "# Mes Favoris\n\nAucun favori enregistré."
    
    lines = [
        "# 📚 Mes Favoris - MCP Veille V3",
        "",
        f"*Exporté le {datetime.now().strftime('%Y-%m-%d à %H:%M')}*",
        "",
        f"**Total : {len(favoris)} article(s)**",
        "",
        "---",
        ""
    ]
    
    # Grouper par thématique si disponible
    par_thematique = {}
    sans_thematique = []
    
    for fav in favoris:
        theme = fav.get('thematique', '').strip()
        if theme:
            if theme not in par_thematique:
                par_thematique[theme] = []
            par_thematique[theme].append(fav)
        else:
            sans_thematique.append(fav)
    
    # Afficher par thématique
    for theme, articles in sorted(par_thematique.items()):
        lines.append(f"## 🎯 {theme}")
        lines.append("")
        
        for fav in articles:
            lines.append(f"### [{fav['titre']}]({fav['url']})")
            lines.append("")
            if fav.get('source'):
                lines.append(f"**Source :** {fav['source']}")
            if fav.get('date_article'):
                lines.append(f"**Date article :** {fav['date_article'][:10] if fav['date_article'] else 'N/A'}")
            lines.append(f"**Ajouté le :** {fav['date_ajout'][:10]}")
            if fav.get('description'):
                lines.append("")
                lines.append(f"> {fav['description']}")
            if fav.get('tags'):
                lines.append("")
                tags = [f"`{tag.strip()}`" for tag in fav['tags'].split(',')]
                lines.append(f"**Tags :** {' '.join(tags)}")
            lines.append("")
            lines.append("---")
            lines.append("")
    
    # Articles sans thématique
    if sans_thematique:
        lines.append("## 📌 Autres articles")
        lines.append("")
        
        for fav in sans_thematique:
            lines.append(f"### [{fav['titre']}]({fav['url']})")
            lines.append("")
            if fav.get('source'):
                lines.append(f"**Source :** {fav['source']}")
            if fav.get('date_article'):
                lines.append(f"**Date article :** {fav['date_article'][:10] if fav['date_article'] else 'N/A'}")
            lines.append(f"**Ajouté le :** {fav['date_ajout'][:10]}")
            if fav.get('description'):
                lines.append("")
                lines.append(f"> {fav['description']}")
            if fav.get('tags'):
                lines.append("")
                tags = [f"`{tag.strip()}`" for tag in fav['tags'].split(',')]
                lines.append(f"**Tags :** {' '.join(tags)}")
            lines.append("")
            lines.append("---")
            lines.append("")
    
    return "\n".join(lines)


def supprimer_favori(favori_id: int) -> bool:
    """Supprime un favori par son ID."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM favoris WHERE id = ?", (favori_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Erreur suppression: {e}")
        return False
    finally:
        conn.close()


def supprimer_historique(historique_id: int) -> bool:
    """Supprime une entrée de l'historique des recherches par son ID."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM historique_recherches WHERE id = ?", (historique_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Erreur suppression historique: {e}")
        return False
    finally:
        conn.close()


def supprimer_rapport(rapport_id: int) -> bool:
    """Supprime un rapport par son ID."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rapports WHERE id = ?", (rapport_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Erreur suppression rapport: {e}")
        return False
    finally:
        conn.close()


def get_historique(limite: int = 50) -> list:
    """Récupère l'historique des recherches avec indication des rapports associés."""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM historique_recherches 
            ORDER BY date_recherche DESC LIMIT ?
        """, (limite,))
        historique = [dict(row) for row in cursor.fetchall()]
        
        # Récupérer tous les rapports pour faire le matching
        cursor.execute("SELECT id, type, titre, date_creation FROM rapports")
        rapports = [dict(row) for row in cursor.fetchall()]
        
        # Associer les rapports aux recherches
        for item in historique:
            item['has_rapport'] = False
            item['rapport_id'] = None
            
            # Chercher un rapport correspondant (même type/query et date proche)
            for rapport in rapports:
                # Le titre du rapport contient généralement la query
                rapport_titre = rapport.get('titre', '') or ''
                rapport_type = rapport.get('type', '')
                
                # Vérifier si le rapport correspond à cette recherche
                if item['query'] and item['query'] in rapport_titre:
                    # Vérifier que les dates sont proches (même jour)
                    try:
                        date_recherche = item['date_recherche'][:10]
                        date_rapport = rapport['date_creation'][:10]
                        if date_recherche == date_rapport:
                            item['has_rapport'] = True
                            item['rapport_id'] = rapport['id']
                            break
                    except:
                        pass
        
        return historique
    except Exception as e:
        st.error(f"Erreur lecture historique: {e}")
        return []
    finally:
        conn.close()


def get_rapports(limite: int = 20) -> list:
    """Récupère les rapports générés."""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, type, titre, date_creation, 
                   substr(contenu, 1, 500) as apercu,
                   CASE WHEN analyse IS NOT NULL AND analyse != '' THEN 1 ELSE 0 END as has_analyse
            FROM rapports 
            ORDER BY date_creation DESC LIMIT ?
        """, (limite,))
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        st.error(f"Erreur lecture rapports: {e}")
        return []
    finally:
        conn.close()


def get_rapport_complet(rapport_id: int) -> Optional[dict]:
    """Récupère un rapport complet par son ID."""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rapports WHERE id = ?", (rapport_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        st.error(f"Erreur lecture rapport: {e}")
        return None
    finally:
        conn.close()


def get_statistiques() -> dict:
    """Calcule les statistiques d'utilisation."""
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM favoris")
        nb_favoris = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM historique_recherches")
        nb_recherches = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM rapports")
        nb_rapports = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM historique_recherches 
            GROUP BY type
        """)
        recherches_par_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("SELECT MAX(date_recherche) FROM historique_recherches")
        derniere_recherche = cursor.fetchone()[0]
        
        return {
            "favoris": nb_favoris,
            "recherches": nb_recherches,
            "rapports": nb_rapports,
            "recherches_par_type": recherches_par_type,
            "derniere_activite": derniere_recherche
        }
    except Exception as e:
        st.error(f"Erreur calcul stats: {e}")
        return {}
    finally:
        conn.close()


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def parse_articles_from_rapport(contenu: str) -> List[Dict]:
    """
    Parse le contenu d'un rapport pour extraire les articles.
    Retourne une liste de dictionnaires avec titre, source, date, url, description.
    """
    articles = []
    
    if not contenu:
        return articles
    
    lines = contenu.split('\n')
    current_article = {}
    
    for line in lines:
        line = line.strip()
        
        # Détecter un nouvel article (commence par un numéro suivi d'un point)
        match_titre = re.match(r'^(\d+)\.\s+(.+)$', line)
        if match_titre:
            # Sauvegarder l'article précédent s'il existe
            if current_article.get('titre'):
                articles.append(current_article)
            
            current_article = {
                'titre': match_titre.group(2),
                'source': '',
                'date': '',
                'url': '',
                'description': ''
            }
            continue
        
        # Extraire source et date (ligne avec 📰 et 📅)
        if '📰' in line and current_article:
            # Format: 📰 Source | 📅 Date
            parts = line.replace('📰', '').replace('📅', '').split('|')
            if len(parts) >= 1:
                current_article['source'] = parts[0].strip()
            if len(parts) >= 2:
                current_article['date'] = parts[1].strip()
            continue
        
        # Extraire URL (ligne avec 🔗)
        if '🔗' in line and current_article:
            url = line.replace('🔗', '').strip()
            if url.startswith('http'):
                current_article['url'] = url
            continue
        
        # Extraire description (ligne avec 💬)
        if '💬' in line and current_article:
            current_article['description'] = line.replace('💬', '').strip()
            continue
    
    # Ajouter le dernier article
    if current_article.get('titre'):
        articles.append(current_article)
    
    return articles


# =============================================================================
# INTERFACE STREAMLIT
# =============================================================================

def main():
    """Point d'entrée principal du dashboard."""
    
    # Sidebar - Navigation (pages simplifiées)
    st.sidebar.title("🔍 MCP Veille V3")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["📊 Dashboard", "⭐ Favoris", "📜 Historique", "📄 Rapports"]
    )
    
    st.sidebar.markdown("---")
    
    # Statistiques rapides dans la sidebar
    stats = get_statistiques()
    if stats:
        st.sidebar.markdown("### 📈 Statistiques")
        col1, col2 = st.sidebar.columns(2)
        col1.metric("Favoris", stats.get("favoris", 0))
        col2.metric("Recherches", stats.get("recherches", 0))
        st.sidebar.metric("Rapports", stats.get("rapports", 0))
        
        if stats.get("derniere_activite"):
            st.sidebar.caption(f"Dernière activité: {stats['derniere_activite'][:16]}")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("💡 Utilisez Claude Desktop pour lancer des veilles et analyses")
    
    # Contenu principal selon la page
    if page == "📊 Dashboard":
        page_dashboard(stats)
    elif page == "⭐ Favoris":
        page_favoris()
    elif page == "📜 Historique":
        page_historique()
    elif page == "📄 Rapports":
        page_rapports()


def page_dashboard(stats: dict):
    """Page d'accueil avec vue d'ensemble."""
    st.title("📊 Dashboard de Veille Technologique")
    st.markdown("Bienvenue dans votre système de veille MCP V3. Cette interface partage les données avec Claude Desktop.")
    
    st.markdown("---")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("⭐ Favoris", stats.get("favoris", 0))
    col2.metric("🔍 Recherches", stats.get("recherches", 0))
    col3.metric("📄 Rapports", stats.get("rapports", 0))
    
    recherches_type = stats.get("recherches_par_type", {})
    total_thematiques = recherches_type.get("thematique", 0)
    col4.metric("🎯 Veilles thématiques", total_thematiques)
    
    st.markdown("---")
    
    # Derniers favoris et activité récente
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("⭐ Derniers favoris")
        favoris = get_favoris(limite=5)
        
        if favoris:
            for fav in favoris:
                with st.container():
                    st.markdown(f"**{fav['titre'][:60]}{'...' if len(fav['titre']) > 60 else ''}**")
                    st.caption(f"📰 {fav.get('source', 'N/A')} | 📅 {fav['date_ajout'][:10]}")
                    st.markdown(f"[🔗 Lire l'article]({fav['url']})")
                    st.markdown("---")
        else:
            st.info("Aucun favori pour le moment. Ajoutez-en via Claude Desktop ou depuis les rapports !")
    
    with col_right:
        st.subheader("📜 Activité récente")
        historique = get_historique(limite=5)
        
        if historique:
            for item in historique:
                type_emoji = {"recherche": "🔍", "thematique": "🎯", "rss": "📡"}.get(item['type'], "📌")
                rapport_badge = " 📄" if item.get('has_rapport') else ""
                st.markdown(f"{type_emoji} **{item['type'].capitalize()}**: {item['query'] or 'N/A'}{rapport_badge}")
                st.caption(f"📅 {item['date_recherche'][:16]} | 📊 {item['nb_resultats']} résultats")
                st.markdown("---")
        else:
            st.info("Aucune activité enregistrée.")
    
    # Thématiques disponibles
    st.markdown("---")
    st.subheader("🎯 Thématiques disponibles")
    
    col_ia, col_pro = st.columns(2)
    
    with col_ia:
        st.markdown("**🤖 Bloc IA**")
        for nom, info in THEMATIQUES.items():
            if info["categorie"] == "IA":
                st.markdown(f"• **{nom}**: {info['description']}")
    
    with col_pro:
        st.markdown("**💼 Bloc Professionnel**")
        for nom, info in THEMATIQUES.items():
            if info["categorie"] == "PRO":
                st.markdown(f"• **{nom}**: {info['description']}")


def page_favoris():
    """Page de gestion des favoris."""
    st.title("⭐ Mes Favoris")
    
    # Barre de recherche et bouton export
    col_search, col_export = st.columns([0.8, 0.2])
    
    with col_search:
        search = st.text_input("🔍 Rechercher dans les favoris", placeholder="Titre, description ou tags...")
    
    with col_export:
        st.markdown("")  # Espacement
        if st.button("📥 Exporter (.md)", help="Exporter tous les favoris au format Markdown"):
            markdown_content = exporter_favoris_markdown()
            st.download_button(
                label="💾 Télécharger",
                data=markdown_content,
                file_name=f"favoris_veille_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                key="download_md"
            )
    
    favoris = get_favoris(limite=100, search=search if search else None)
    
    if not favoris:
        st.info("Aucun favori trouvé." if search else "Aucun favori enregistré. Ajoutez-en via Claude Desktop ou depuis les rapports !")
        return
    
    st.markdown(f"**{len(favoris)} favori(s) trouvé(s)**")
    st.markdown("---")
    
    # Affichage des favoris
    for fav in favoris:
        with st.container():
            col1, col2 = st.columns([0.9, 0.1])
            
            with col1:
                st.markdown(f"### {fav['titre']}")
                st.markdown(f"📰 **{fav.get('source', 'Source inconnue')}** | 📅 Ajouté le {fav['date_ajout'][:10]}")
                
                if fav.get('description'):
                    st.markdown(f"💬 {fav['description']}")
                
                if fav.get('tags'):
                    tags = fav['tags'].split(',')
                    st.markdown("🏷️ " + " ".join([f"`{tag.strip()}`" for tag in tags]))
                
                st.markdown(f"[🔗 Ouvrir l'article]({fav['url']})")
            
            with col2:
                if st.button("🗑️", key=f"del_{fav['id']}", help="Supprimer ce favori"):
                    if supprimer_favori(fav['id']):
                        st.success("Favori supprimé !")
                        st.rerun()
            
            st.markdown("---")


def page_historique():
    """Page d'historique des recherches avec indication des rapports."""
    st.title("📜 Historique des Recherches")
    
    historique = get_historique(limite=100)
    
    if not historique:
        st.info("Aucune recherche enregistrée.")
        return
    
    # Filtres
    col1, col2 = st.columns(2)
    
    with col1:
        types_disponibles = list(set(h['type'] for h in historique))
        filtre_type = st.selectbox("Filtrer par type", ["Tous"] + types_disponibles)
    
    with col2:
        filtre_rapport = st.selectbox("Filtrer par rapport", ["Tous", "Avec rapport 📄", "Sans rapport"])
    
    # Appliquer les filtres
    historique_filtre = historique
    
    if filtre_type != "Tous":
        historique_filtre = [h for h in historique_filtre if h['type'] == filtre_type]
    
    if filtre_rapport == "Avec rapport 📄":
        historique_filtre = [h for h in historique_filtre if h.get('has_rapport')]
    elif filtre_rapport == "Sans rapport":
        historique_filtre = [h for h in historique_filtre if not h.get('has_rapport')]
    
    st.markdown(f"**{len(historique_filtre)} recherche(s)**")
    st.markdown("---")
    
    # Affichage sous forme de liste avec expander pour les rapports
    for item in historique_filtre:
        type_emoji = {"recherche": "🔍", "thematique": "🎯", "rss": "📡"}.get(item['type'], "📌")
        rapport_badge = " 📄" if item.get('has_rapport') else ""
        
        # Ligne avec titre et bouton supprimer
        col_title, col_del = st.columns([0.95, 0.05])
        
        with col_del:
            if st.button("🗑️", key=f"del_hist_{item['id']}", help="Supprimer cette recherche"):
                if supprimer_historique(item['id']):
                    st.success("Recherche supprimée !")
                    st.rerun()
        
        # Titre de l'expander
        expander_title = f"{type_emoji} **{item['type'].capitalize()}** : {item['query'] or 'N/A'} — 📅 {item['date_recherche'][:16]} — 📊 {item['nb_resultats']} résultats{rapport_badge}"
        
        with st.expander(expander_title):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Type:** {item['type']}")
                st.markdown(f"**Requête:** {item['query'] or 'N/A'}")
            with col2:
                st.markdown(f"**Date:** {item['date_recherche'][:16]}")
                st.markdown(f"**Résultats:** {item['nb_resultats']}")
            
            # Si un rapport est associé, l'afficher directement
            if item.get('has_rapport') and item.get('rapport_id'):
                st.markdown("---")
                st.markdown("### 📄 Rapport associé")
                
                rapport = get_rapport_complet(item['rapport_id'])
                if rapport:
                    # Récupérer les URLs des favoris
                    urls_favoris = get_favoris_urls()
                    
                    # Onglets pour le contenu du rapport
                    tab1, tab2 = st.tabs(["📋 Articles", "🤖 Analyse Claude"])
                    
                    with tab1:
                        st.caption("⭐ = en favori | ☆ = cliquez pour ajouter")
                        articles = parse_articles_from_rapport(rapport.get('contenu', ''))
                        if articles:
                            for i, article in enumerate(articles):
                                col_art, col_fav = st.columns([0.85, 0.15])
                                
                                with col_art:
                                    st.markdown(f"**{i+1}. {article['titre']}**")
                                    if article['source'] or article['date']:
                                        st.caption(f"📰 {article['source']} | 📅 {article['date']}")
                                    if article['url']:
                                        st.markdown(f"[🔗 Lire]({article['url']})")
                                
                                with col_fav:
                                    if article['url']:
                                        is_favori = article['url'] in urls_favoris
                                        
                                        if is_favori:
                                            st.markdown("### ⭐")
                                        else:
                                            if st.button("☆", key=f"fav_hist_{item['id']}_{i}", help="Ajouter aux favoris"):
                                                result = ajouter_favori(
                                                    url=article['url'],
                                                    titre=article['titre'],
                                                    source=article['source'],
                                                    description=article.get('description', ''),
                                                    date_article=article['date'],
                                                    thematique=rapport.get('titre', '')
                                                )
                                                if result['success']:
                                                    st.rerun()
                        else:
                            st.info("Aucun article parsé dans ce rapport.")
                    
                    with tab2:
                        if rapport.get('analyse'):
                            st.markdown(rapport['analyse'])
                        else:
                            st.info("Pas d'analyse Claude pour ce rapport.")
                else:
                    st.warning("Rapport introuvable.")


def page_rapports():
    """Page de visualisation des rapports avec possibilité d'ajouter aux favoris."""
    st.title("📄 Rapports Générés")
    
    rapports = get_rapports(limite=20)
    
    if not rapports:
        st.info("Aucun rapport généré. Utilisez 'generer_rapport' dans Claude Desktop.")
        return
    
    # Sélection du rapport avec bouton supprimer
    col_select, col_del = st.columns([0.9, 0.1])
    
    with col_select:
        options = {f"{r['id']} - {r['titre'] or r['type']} ({r['date_creation'][:10]})": r['id'] for r in rapports}
        selection = st.selectbox("Sélectionner un rapport", list(options.keys()))
    
    if selection:
        rapport_id = options[selection]
        
        with col_del:
            st.markdown("")  # Espacement pour aligner avec le selectbox
            if st.button("🗑️", key=f"del_rapport_{rapport_id}", help="Supprimer ce rapport"):
                if supprimer_rapport(rapport_id):
                    st.success("Rapport supprimé !")
                    st.rerun()
        
        rapport = get_rapport_complet(rapport_id)
        
        if rapport:
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Type", rapport['type'])
            col2.metric("Date", rapport['date_creation'][:10])
            col3.metric("Analyse IA", "✅ Oui" if rapport.get('analyse') else "❌ Non")
            
            st.markdown("---")
            
            # Onglets pour le contenu
            tab1, tab2, tab3 = st.tabs(["📋 Articles", "🤖 Analyse Claude", "📝 Contenu brut"])
            
            with tab1:
                st.subheader("Articles du rapport")
                st.markdown("⭐ = en favori | ☆ = cliquez pour ajouter")
                st.markdown("---")
                
                # Récupérer toutes les URLs des favoris pour vérification rapide
                urls_favoris = get_favoris_urls()
                
                # Parser les articles du rapport
                articles = parse_articles_from_rapport(rapport.get('contenu', ''))
                
                if articles:
                    for i, article in enumerate(articles):
                        col_art, col_fav = st.columns([0.9, 0.1])
                        
                        with col_art:
                            st.markdown(f"**{i+1}. {article['titre']}**")
                            if article['source'] or article['date']:
                                st.caption(f"📰 {article['source']} | 📅 {article['date']}")
                            if article['description']:
                                st.markdown(f"💬 {article['description']}")
                            if article['url']:
                                st.markdown(f"[🔗 Lire l'article]({article['url']})")
                        
                        with col_fav:
                            if article['url']:
                                is_favori = article['url'] in urls_favoris
                                
                                if is_favori:
                                    st.markdown("### ⭐")
                                else:
                                    if st.button("☆", key=f"fav_{rapport_id}_{i}", help="Ajouter aux favoris"):
                                        result = ajouter_favori(
                                            url=article['url'],
                                            titre=article['titre'],
                                            source=article['source'],
                                            description=article['description'],
                                            date_article=article['date'],
                                            thematique=rapport.get('titre', '')
                                        )
                                        if result['success']:
                                            st.rerun()
                        
                        st.markdown("---")
                else:
                    st.info("Impossible de parser les articles de ce rapport. Consultez l'onglet 'Contenu brut'.")
            
            with tab2:
                if rapport.get('analyse'):
                    st.markdown(rapport['analyse'])
                else:
                    st.info("Pas d'analyse Claude pour ce rapport.")
            
            with tab3:
                st.text(rapport.get('contenu', 'Contenu non disponible'))


# =============================================================================
# STYLES CSS PERSONNALISÉS
# =============================================================================

def inject_custom_css():
    """Injecte du CSS personnalisé pour améliorer l'apparence."""
    st.markdown("""
    <style>
    /* Métriques avec contraste garanti pour thème sombre et clair */
    [data-testid="stMetric"] {
        background-color: #262730;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #4a4a5a;
    }
    
    [data-testid="stMetric"] label {
        color: #fafafa !important;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
    }
    
    /* Sidebar metrics */
    section[data-testid="stSidebar"] [data-testid="stMetric"] {
        background-color: #1e1e2e;
        border: 1px solid #3a3a4a;
    }
    
    section[data-testid="stSidebar"] [data-testid="stMetric"] label {
        color: #e0e0e0 !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    
    /* Boutons arrondis */
    .stButton>button {
        border-radius: 5px;
    }
    
    /* Titres avec couleur cohérente */
    h1 {
        color: #60a5fa;
    }
    
    /* Conteneurs avec bordure subtile */
    .stContainer {
        border: 1px solid #3a3a4a;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    inject_custom_css()
    main()