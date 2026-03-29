#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Veille V3 - Serveur Principal
=================================

Phase 3 : Capacités de veille complètes
- 6 thématiques préconfigurées (NewsAPI)
- 5 catégories RSS (17 flux)
- Analyse Claude à la demande
- Génération de rapports

Outils disponibles :
- rechercher_actualites : Recherche libre
- lancer_veille_thematique : Veille sur une des 6 thématiques
- lancer_veille_rss : Collecte des flux RSS
- analyser_resultats : Analyse Claude des derniers résultats
- ajouter_favori, lister_favoris, supprimer_favori : Gestion favoris
- voir_thematiques : Liste des thématiques disponibles
- generer_rapport : Créer un rapport complet
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from contextlib import contextmanager

# Import du SDK MCP
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

# Imports pour les APIs
import requests
import feedparser
from dotenv import load_dotenv
from anthropic import Anthropic

# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_DIR = Path(__file__).parent.parent
load_dotenv(PROJECT_DIR / ".env")

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DB_PATH = PROJECT_DIR / "data" / "veille.db"

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("veille-mcp")

# =============================================================================
# THÉMATIQUES PRÉCONFIGURÉES (6)
# =============================================================================

THEMATIQUES = {
    "Claude & Anthropic": {
        "description": "Actualités Anthropic, Claude AI, protocole MCP",
        "keywords": ["Anthropic Claude", "Claude AI", "MCP Anthropic", "Claude Sonnet"],
        "categorie": "IA"
    },
    "Écosystème LLM": {
        "description": "OpenAI, Google Gemini, Mistral,Microsoft, Meta Llama et autres grands modèles",
        "keywords": ["OpenAI", "chatGPT", "Claude", "Anthropic", "Google Gemini", "Mistral AI", "Meta Llama", "Microsoft Copilot", "Qwen", "Deepseek"],
        "categorie": "IA"
    },
    "IA Europe & Réglementation": {
        "description": "AI Act, RGPD appliqué à l'IA, positions CNIL",
        "keywords": ["AI Act Europe", "RGPD intelligence artificielle", "regulation AI Europe"],
        "categorie": "IA"
    },
    "HR Tech & Formation": {
        "description": "Cornerstone, LMS, talent management, formation professionnelle",
        "keywords": ["Cornerstone OnDemand", "HR Technology", "Learning Management System"],
        "categorie": "PRO"
    },
    "Agents IA & Automatisation": {
        "description": "AI Agents, RAG, LangChain, automatisation intelligente",
        "keywords": ["AI Agents autonomous", "LangChain AI", "RAG retrieval augmented","Open webUI"],
        "categorie": "PRO"
    },
    "Open Source & Outils Dev": {
        "description": "Hugging Face, Open WebUI, Ollama, outils développeurs IA",
        "keywords": ["Hugging Face models", "Open WebUI", "Ollama local LLM"],
        "categorie": "PRO"
    }
}

# =============================================================================
# FLUX RSS CONFIGURÉS (5 catégories, 17 flux)
# =============================================================================

RSS_FEEDS = {
    "Actu News tech": [
        {"name": "BDM", "url": "https://www.blogdumoderateur.com/feed/"},
        {"name": "Siècle Digital", "url": "https://siecledigital.fr/feed/"},
        {"name": "The Gradient", "url": "https://thegradient.pub/rss/"},
        {"name": "Developpez", "url": "https://www.developpez.com/index/rss"},
    ],
    "IA & Acteurs majeurs": [
        {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/"},
        {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
        {"name": "DeepMind", "url": "https://deepmind.google/blog/rss.xml"},
        {"name": "AI News", "url": "https://www.artificialintelligence-news.com/feed/"},
    ],
    "Développeur & Open Source": [
        {"name": "GitHub Blog", "url": "https://github.blog/feed/"},
        {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
        {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab"},
    ],
    "Microsoft": [
        {"name": "MS Azure", "url": "https://azure.microsoft.com/en-us/blog/feed/"},
        {"name": "MS Foundry", "url": "https://devblogs.microsoft.com/foundry/feed/"},
        {"name": "MS Power Platform", "url": "https://devblogs.microsoft.com/powerplatform/feed/"},
    ],
    "Réglementation": [
    {"name": "EU AI Act News",          "url": "https://artificialintelligenceact.eu/fr/feed/"},
    {"name": "APD Belgique",            "url": "https://www.autoriteprotectiondonnees.be/rss.xml"},
    {"name": "Village de la Justice",   "url": "https://www.village-justice.com/rss.xml"},
],
}

# =============================================================================
# VARIABLE GLOBALE POUR STOCKER LES DERNIERS RÉSULTATS
# =============================================================================

# Cette variable stocke les derniers résultats de recherche pour l'analyse
derniers_resultats = {
    "type": None,  # "recherche", "thematique", "rss"
    "data": [],
    "timestamp": None,
    "query": None
}

# =============================================================================
# BASE DE DONNÉES
# =============================================================================

def init_database():
    """Initialise la base de données SQLite."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Initialisation base de données: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favoris (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            titre TEXT NOT NULL,
            source TEXT,
            description TEXT,
            date_article TEXT,
            date_ajout TEXT NOT NULL,
            tags TEXT,
            thematique TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historique_recherches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            query TEXT,
            date_recherche TEXT NOT NULL,
            nb_resultats INTEGER,
            parametres TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rapports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            titre TEXT,
            date_creation TEXT NOT NULL,
            contenu TEXT,
            analyse TEXT,
            metadata TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Base de données initialisée")


@contextmanager
def get_db_connection():
    """Context manager pour les connexions DB."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# =============================================================================
# CRÉATION DU SERVEUR MCP
# =============================================================================

server = Server("veille-system")

# =============================================================================
# VALIDATION DES ENTRÉES
# =============================================================================

LANGUES_VALIDES = {"fr", "en", "de", "es", "it", "pt", "nl", "ru", "zh", "ar", "all"}

def valider_parametres(jours: int = None, max_articles: int = None, langue: str = None) -> dict:
    """Valide les paramètres communs et retourne les valeurs corrigées.

    Returns:
        dict avec les clés: jours, max_articles, langue, errors (liste d'avertissements)
    """
    errors = []
    result = {}

    if jours is not None:
        if jours < 1:
            errors.append(f"jours={jours} invalide, utilisation de 1")
            result["jours"] = 1
        elif jours > 30:
            errors.append(f"jours={jours} trop élevé, limité à 30")
            result["jours"] = 30
        else:
            result["jours"] = jours

    if max_articles is not None:
        if max_articles < 1:
            errors.append(f"max_articles={max_articles} invalide, utilisation de 1")
            result["max_articles"] = 1
        elif max_articles > 100:
            errors.append(f"max_articles={max_articles} trop élevé, limité à 100 (limite NewsAPI)")
            result["max_articles"] = 100
        else:
            result["max_articles"] = max_articles

    if langue is not None:
        langue_lower = langue.lower()
        if langue_lower not in LANGUES_VALIDES:
            errors.append(f"langue='{langue}' non reconnue, utilisation de 'fr'")
            result["langue"] = "fr"
        else:
            result["langue"] = langue_lower

    result["errors"] = errors
    return result


# =============================================================================
# FONCTIONS MÉTIER - RECHERCHE NEWSAPI
# =============================================================================

def rechercher_newsapi(query: str, jours: int = 7, max_resultats: int = 10, langue: str = "fr") -> dict:
    """Recherche d'articles via NewsAPI.

    Args:
        query: Mots-clés de recherche
        jours: Période en jours (défaut: 7)
        max_resultats: Nombre max d'articles (défaut: 10)
        langue: Code langue ISO - "fr", "en", ou "all" pour toutes (défaut: "fr")
    """
    global derniers_resultats

    if not NEWS_API_KEY:
        return {"success": False, "error": "NEWS_API_KEY non configurée", "articles": []}

    try:
        date_debut = (datetime.now() - timedelta(days=jours)).strftime("%Y-%m-%d")

        params = {
            "q": query,
            "from": date_debut,
            "sortBy": "publishedAt",
            "pageSize": min(max_resultats, 100),
            "apiKey": NEWS_API_KEY
        }

        # Ajouter le filtre de langue sauf si "all"
        if langue and langue.lower() != "all":
            params["language"] = langue.lower()
        
        logger.info(f"Recherche NewsAPI: '{query}' sur {jours} jours")
        response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") != "ok":
            return {"success": False, "error": data.get("message", "Erreur NewsAPI"), "articles": []}
        
        articles = []
        for art in data.get("articles", []):
            source = art.get("source", {})
            source_name = source.get("name", "Source inconnue") if isinstance(source, dict) else str(source)
            
            articles.append({
                "titre": art.get("title", "Sans titre"),
                "source": source_name,
                "date": art.get("publishedAt", ""),
                "url": art.get("url", ""),
                "description": (art.get("description") or "")[:200]
            })
        
        # Stocker pour analyse ultérieure
        derniers_resultats = {
            "type": "recherche",
            "data": articles,
            "timestamp": datetime.now().isoformat(),
            "query": query
        }
        
        # Enregistrer dans l'historique
        enregistrer_historique("recherche", query, len(articles), {"jours": jours})
        
        return {"success": True, "query": query, "total_articles": len(articles), "articles": articles}
        
    except Exception as e:
        logger.error(f"Erreur NewsAPI: {e}")
        return {"success": False, "error": str(e), "articles": []}


def enregistrer_historique(type_recherche: str, query: str, nb_resultats: int, parametres: dict):
    """Enregistre une recherche dans l'historique."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historique_recherches (type, query, date_recherche, nb_resultats, parametres)
                VALUES (?, ?, ?, ?, ?)
            """, (type_recherche, query, datetime.now().isoformat(), nb_resultats, json.dumps(parametres)))
            conn.commit()
    except Exception as e:
        logger.error(f"Erreur enregistrement historique: {e}")


# =============================================================================
# FONCTIONS MÉTIER - VEILLE THÉMATIQUE
# =============================================================================

def lancer_veille_thematique(nom_thematique: str, jours: int = 7, max_articles: int = 10, langue: str = "fr") -> dict:
    """Lance une veille sur une thématique préconfigurée."""
    global derniers_resultats

    if nom_thematique not in THEMATIQUES:
        return {
            "success": False,
            "error": f"Thématique '{nom_thematique}' inconnue. Utilisez 'voir_thematiques' pour la liste.",
            "articles": []
        }

    thematique = THEMATIQUES[nom_thematique]
    keywords = thematique["keywords"]

    logger.info(f"Veille thématique: {nom_thematique} ({len(keywords)} mots-clés)")

    all_articles = []
    seen_urls = set()

    # Rechercher avec chaque mot-clé (limiter à 2 pour éviter trop de requêtes)
    for keyword in keywords[:2]:
        result = rechercher_newsapi(keyword, jours=jours, max_resultats=max_articles, langue=langue)
        
        if result["success"]:
            for art in result["articles"]:
                url = art.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    art["thematique"] = nom_thematique
                    all_articles.append(art)
    
    # Limiter au nombre demandé
    all_articles = all_articles[:max_articles]
    
    # Stocker pour analyse
    derniers_resultats = {
        "type": "thematique",
        "data": all_articles,
        "timestamp": datetime.now().isoformat(),
        "query": nom_thematique
    }
    
    enregistrer_historique("thematique", nom_thematique, len(all_articles), {"jours": jours})
    
    return {
        "success": True,
        "thematique": nom_thematique,
        "description": thematique["description"],
        "categorie": thematique["categorie"],
        "total_articles": len(all_articles),
        "articles": all_articles
    }


# =============================================================================
# FONCTIONS MÉTIER - VEILLE RSS
# =============================================================================

def lancer_veille_rss(jours: int = 3, categorie: str = None) -> dict:
    """Collecte les articles des flux RSS configurés."""
    global derniers_resultats
    
    logger.info(f"Veille RSS: {jours} jours, catégorie: {categorie or 'toutes'}")
    
    all_articles = []
    seen_urls = set()
    cutoff_date = datetime.now() - timedelta(days=jours)
    
    feeds_to_check = RSS_FEEDS
    if categorie:
        feeds_to_check = {k: v for k, v in RSS_FEEDS.items() if k.lower() == categorie.lower()}
    
    for cat_name, feeds in feeds_to_check.items():
        for feed_info in feeds:
            try:
                logger.info(f"Parsing RSS: {feed_info['name']}")
                feed = feedparser.parse(feed_info["url"])
                
                if feed.bozo:
                    logger.warning(f"Flux RSS mal formé: {feed_info['name']}")
                    continue
                
                for entry in feed.entries[:10]:  # Limiter à 10 par flux
                    # Extraire la date
                    published = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6])
                    
                    # Filtrer par date
                    if published and published < cutoff_date:
                        continue
                    
                    url = entry.get('link', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        
                        article = {
                            "titre": entry.get('title', 'Sans titre'),
                            "source": feed_info['name'],
                            "categorie_rss": cat_name,
                            "date": published.isoformat() if published else "",
                            "url": url,
                            "description": (entry.get('summary', '') or entry.get('description', ''))[:200]
                        }
                        all_articles.append(article)
                        
            except Exception as e:
                logger.error(f"Erreur flux {feed_info['name']}: {e}")
    
    # Trier par date (plus récent en premier)
    all_articles.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Stocker pour analyse
    derniers_resultats = {
        "type": "rss",
        "data": all_articles,
        "timestamp": datetime.now().isoformat(),
        "query": f"RSS {categorie or 'toutes catégories'}"
    }
    
    enregistrer_historique("rss", categorie or "toutes", len(all_articles), {"jours": jours})
    
    return {
        "success": True,
        "total_articles": len(all_articles),
        "categories": list(feeds_to_check.keys()),
        "articles": all_articles
    }


# =============================================================================
# FONCTIONS MÉTIER - ANALYSE CLAUDE
# =============================================================================

def analyser_avec_claude(articles: list, contexte: str = "") -> dict:
    """Analyse les articles avec Claude."""
    
    if not ANTHROPIC_API_KEY:
        return {"success": False, "error": "ANTHROPIC_API_KEY non configurée"}
    
    if not articles:
        return {"success": False, "error": "Aucun article à analyser"}
    
    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Préparer le contenu des articles
        articles_text = ""
        for i, art in enumerate(articles[:20], 1):  # Limiter à 20 articles
            articles_text += f"""
{i}. {art.get('titre', 'N/A')}
   Source: {art.get('source', 'N/A')} | Date: {art.get('date', 'N/A')[:10] if art.get('date') else 'N/A'}
   URL: {art.get('url', 'N/A')}
   Description: {art.get('description', 'N/A')}
"""
        
        prompt = f"""Tu es un expert en veille technologique. Analyse ces {len(articles)} articles{' sur ' + contexte if contexte else ''} et fournis :

1. **SYNTHÈSE GÉNÉRALE** (3-4 phrases)
   - Vue d'ensemble des actualités
   - Tendance dominante

2. **POINTS CLÉS** (3-5 points)
   - Les informations les plus importantes
   - Signaux faibles à surveiller

3. **LECTURES PRIORITAIRES** (3-5 articles)
   - Liste uniquement les titres des articles les plus importants
   - Format: "• Titre de l'article - Source"

4. **RECOMMANDATIONS** (2-3 actions)
   - Actions concrètes suggérées

Articles à analyser :
{articles_text}

Sois concis et actionnable."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analyse = response.content[0].text
        
        return {
            "success": True,
            "analyse": analyse,
            "nb_articles_analyses": len(articles[:20])
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse Claude: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# FONCTIONS MÉTIER - FAVORIS
# =============================================================================

def ajouter_favori(url: str, titre: str, source: str = "", description: str = "", 
                   date_article: str = "", tags: str = "", thematique: str = "") -> dict:
    """Ajoute un article aux favoris."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
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


def lister_favoris(limite: int = 20) -> dict:
    """Liste les favoris."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, url, titre, source, description, date_article, date_ajout, tags, thematique
                FROM favoris ORDER BY date_ajout DESC LIMIT ?
            """, (limite,))
            
            favoris = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT COUNT(*) FROM favoris")
            total = cursor.fetchone()[0]
            
            return {"success": True, "favoris": favoris, "total": total}
    except Exception as e:
        return {"success": False, "error": str(e), "favoris": []}


def supprimer_favori(favori_id: int = None, url: str = None) -> dict:
    """Supprime un favori."""
    if not favori_id and not url:
        return {"success": False, "error": "Spécifiez un ID ou une URL"}
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if favori_id:
                cursor.execute("DELETE FROM favoris WHERE id = ?", (favori_id,))
            else:
                cursor.execute("DELETE FROM favoris WHERE url = ?", (url,))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                return {"success": True, "message": "Favori supprimé"}
            return {"success": False, "error": "Favori non trouvé"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# FONCTIONS MÉTIER - RAPPORTS
# =============================================================================

def generer_rapport(type_rapport: str = "complet", inclure_analyse: bool = True) -> dict:
    """Génère un rapport de veille complet."""
    global derniers_resultats
    
    if not derniers_resultats["data"]:
        return {"success": False, "error": "Aucune donnée à inclure. Lancez d'abord une veille."}
    
    articles = derniers_resultats["data"]
    
    # Construire le rapport
    rapport_lines = [
        "=" * 60,
        "RAPPORT DE VEILLE TECHNOLOGIQUE",
        "=" * 60,
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Type: {derniers_resultats['type']}",
        f"Contexte: {derniers_resultats['query']}",
        f"Articles: {len(articles)}",
        "=" * 60,
        ""
    ]
    
    for i, art in enumerate(articles, 1):
        rapport_lines.append(f"{i}. {art.get('titre', 'N/A')}")
        rapport_lines.append(f"   📰 {art.get('source', 'N/A')} | 📅 {art.get('date', 'N/A')[:10] if art.get('date') else 'N/A'}")
        rapport_lines.append(f"   🔗 {art.get('url', 'N/A')}")
        if art.get('description'):
            rapport_lines.append(f"   💬 {art['description']}")
        rapport_lines.append("")
    
    rapport_contenu = "\n".join(rapport_lines)
    
    # Analyse optionnelle
    analyse = ""
    if inclure_analyse:
        result_analyse = analyser_avec_claude(articles, derniers_resultats['query'])
        if result_analyse["success"]:
            analyse = result_analyse["analyse"]
    
    # Sauvegarder en base
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rapports (type, titre, date_creation, contenu, analyse, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                derniers_resultats['type'],
                f"Rapport {derniers_resultats['query']}",
                datetime.now().isoformat(),
                rapport_contenu,
                analyse,
                json.dumps({"nb_articles": len(articles)})
            ))
            conn.commit()
            rapport_id = cursor.lastrowid
    except Exception as e:
        logger.error(f"Erreur sauvegarde rapport: {e}")
        rapport_id = None
    
    return {
        "success": True,
        "rapport_id": rapport_id,
        "contenu": rapport_contenu,
        "analyse": analyse,
        "nb_articles": len(articles)
    }


# =============================================================================
# OUTILS MCP
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Déclare tous les outils MCP disponibles."""
    
    return [
        # Recherche libre
        Tool(
            name="rechercher_actualites",
            description="""Recherche des actualités sur un sujet libre.
Utilise quand l'utilisateur veut chercher sur un sujet spécifique non couvert par les thématiques.
Exemples: "Cherche des news sur quantum computing", "Actualités Tesla cette semaine" """,
            inputSchema={
                "type": "object",
                "properties": {
                    "sujet": {"type": "string", "description": "Mots-clés de recherche"},
                    "jours": {"type": "integer", "description": "Période en jours (défaut: 7)", "default": 7},
                    "max_articles": {"type": "integer", "description": "Nombre max d'articles (défaut: 10)", "default": 10},
                    "langue": {"type": "string", "description": "Langue: 'fr' (défaut), 'en', ou 'all' pour toutes", "default": "fr"}
                },
                "required": ["sujet"]
            }
        ),
        
        # Veille thématique
        Tool(
            name="lancer_veille_thematique",
            description="""Lance une veille sur une des 6 thématiques préconfigurées.
Thématiques disponibles:
- "Claude & Anthropic" : Actualités Claude, Anthropic, MCP
- "Écosystème LLM" : OpenAI, Gemini, Mistral, Llama
- "IA Europe & Réglementation" : AI Act, RGPD, CNIL
- "HR Tech & Formation" : Cornerstone, LMS, RH
- "Agents IA & Automatisation" : AI Agents, RAG, LangChain
- "Open Source & Outils Dev" : Hugging Face, Open WebUI, Ollama

Exemples: "Lance une veille sur Claude & Anthropic", "Veille thématique Écosystème LLM" """,
            inputSchema={
                "type": "object",
                "properties": {
                    "thematique": {"type": "string", "description": "Nom exact de la thématique"},
                    "jours": {"type": "integer", "description": "Période en jours (défaut: 7)", "default": 7},
                    "max_articles": {"type": "integer", "description": "Nombre max d'articles (défaut: 10)", "default": 10},
                    "langue": {"type": "string", "description": "Langue: 'fr' (défaut), 'en', ou 'all' pour toutes", "default": "fr"}
                },
                "required": ["thematique"]
            }
        ),
        
        # Voir thématiques
        Tool(
            name="voir_thematiques",
            description="""Liste les thématiques de veille disponibles avec leurs descriptions.
Utilise quand l'utilisateur demande la liste des thématiques ou ne sait pas laquelle choisir.""",
            inputSchema={"type": "object", "properties": {}}
        ),
        
        # Veille RSS
        Tool(
            name="lancer_veille_rss",
            description="""Collecte les derniers articles des flux RSS configurés.
5 catégories disponibles:
- "Actu News tech" : BDM, Siècle Digital, The Gradient, Developpez
- "IA & Acteurs majeurs" : Google AI Blog, OpenAI Blog, DeepMind, AI News
- "Développeur & Open Source" : GitHub Blog, Hugging Face Blog, Ars Technica
- "Microsoft" : MS Azure, MS Foundry, MS Power Platform
- "Réglementation" : EU AI Act News, APD Belgique, Village de la Justice

Exemples: "Lance la veille RSS", "Collecte les flux RSS Microsoft" """,
            inputSchema={
                "type": "object",
                "properties": {
                    "jours": {"type": "integer", "description": "Période en jours (défaut: 3)", "default": 3},
                    "categorie": {"type": "string", "description": "Catégorie spécifique (optionnel)"}
                }
            }
        ),
        
        # Analyse Claude
        Tool(
            name="analyser_resultats",
            description="""Analyse les derniers résultats de recherche avec Claude.
Lance une analyse IA des articles trouvés lors de la dernière recherche, veille thématique ou RSS.
Fournit: synthèse, points clés, lectures prioritaires, recommandations.

Exemples: "Analyse les résultats", "Fais une synthèse des articles trouvés" """,
            inputSchema={"type": "object", "properties": {}}
        ),
        
        # Génération rapport
        Tool(
            name="generer_rapport",
            description="""Génère un rapport complet des derniers résultats.
Crée un rapport structuré avec tous les articles et optionnellement une analyse Claude.
Le rapport est sauvegardé en base de données.

Exemples: "Génère un rapport", "Crée un rapport de veille" """,
            inputSchema={
                "type": "object",
                "properties": {
                    "inclure_analyse": {"type": "boolean", "description": "Inclure analyse Claude (défaut: true)", "default": True}
                }
            }
        ),
        
        # Favoris
        Tool(
            name="ajouter_favori",
            description="Ajoute un article aux favoris. Exemples: 'Garde cet article', 'Ajoute le premier à mes favoris'",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL de l'article"},
                    "titre": {"type": "string", "description": "Titre de l'article"},
                    "source": {"type": "string", "description": "Source (optionnel)"},
                    "description": {"type": "string", "description": "Description (optionnel)"},
                    "tags": {"type": "string", "description": "Tags séparés par virgules (optionnel)"}
                },
                "required": ["url", "titre"]
            }
        ),
        
        Tool(
            name="lister_favoris",
            description="Liste les articles favoris. Exemples: 'Montre mes favoris', 'Quels articles j'ai sauvegardés?'",
            inputSchema={
                "type": "object",
                "properties": {
                    "limite": {"type": "integer", "description": "Nombre max (défaut: 20)", "default": 20}
                }
            }
        ),
        
        Tool(
            name="supprimer_favori",
            description="Supprime un favori par ID ou URL. Exemples: 'Retire le favori 3', 'Supprime ce favori'",
            inputSchema={
                "type": "object",
                "properties": {
                    "favori_id": {"type": "integer", "description": "ID du favori"},
                    "url": {"type": "string", "description": "URL de l'article (alternative)"}
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Exécute un outil MCP."""
    
    logger.info(f"Outil appelé: {name} avec {arguments}")
    
    # --- Recherche libre ---
    if name == "rechercher_actualites":
        sujet = arguments.get("sujet", "")
        if not sujet:
            return [TextContent(type="text", text="❌ Veuillez spécifier un sujet de recherche.")]

        # Validation des paramètres
        params = valider_parametres(
            jours=arguments.get("jours", 7),
            max_articles=arguments.get("max_articles", 10),
            langue=arguments.get("langue", "fr")
        )

        result = rechercher_newsapi(
            sujet,
            params["jours"],
            params["max_articles"],
            params["langue"]
        )

        if not result["success"]:
            return [TextContent(type="text", text=f"❌ Erreur: {result['error']}")]

        if not result["articles"]:
            return [TextContent(type="text", text=f"🔍 Aucun article trouvé pour '{sujet}'.")]

        # Ajouter les avertissements de validation si présents
        warnings = ""
        if params["errors"]:
            warnings = "⚠️ " + " | ".join(params["errors"]) + "\n\n"

        response = formater_resultats_recherche(result["articles"], f"Recherche: {sujet}")
        return [TextContent(type="text", text=warnings + response)]

    # --- Veille thématique ---
    elif name == "lancer_veille_thematique":
        thematique = arguments.get("thematique", "")
        if not thematique:
            return [TextContent(type="text", text="❌ Veuillez spécifier une thématique.")]

        # Validation des paramètres
        params = valider_parametres(
            jours=arguments.get("jours", 7),
            max_articles=arguments.get("max_articles", 10),
            langue=arguments.get("langue", "fr")
        )

        result = lancer_veille_thematique(
            thematique,
            params["jours"],
            params["max_articles"],
            params["langue"]
        )

        if not result["success"]:
            return [TextContent(type="text", text=f"❌ {result['error']}")]

        # Ajouter les avertissements de validation si présents
        warnings = ""
        if params["errors"]:
            warnings = "⚠️ " + " | ".join(params["errors"]) + "\n\n"

        response = formater_resultats_recherche(
            result["articles"],
            f"🎯 Thématique: {result['thematique']}\n📋 {result['description']}"
        )
        return [TextContent(type="text", text=warnings + response)]
    
    # --- Voir thématiques ---
    elif name == "voir_thematiques":
        lines = ["📚 **Thématiques de veille disponibles**\n"]
        
        lines.append("**🤖 Bloc IA:**")
        for nom, info in THEMATIQUES.items():
            if info["categorie"] == "IA":
                lines.append(f"• **{nom}** — {info['description']}")
        
        lines.append("\n**💼 Bloc Professionnel:**")
        for nom, info in THEMATIQUES.items():
            if info["categorie"] == "PRO":
                lines.append(f"• **{nom}** — {info['description']}")
        
        lines.append("\n💡 *Utilisez 'lancer_veille_thematique' avec le nom exact de la thématique.*")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    # --- Veille RSS ---
    elif name == "lancer_veille_rss":
        # Validation du paramètre jours
        params = valider_parametres(jours=arguments.get("jours", 3))
        jours = params["jours"]

        result = lancer_veille_rss(jours, arguments.get("categorie"))

        if not result["success"]:
            return [TextContent(type="text", text=f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")]

        if not result["articles"]:
            return [TextContent(type="text", text="📭 Aucun article RSS trouvé pour cette période.")]

        # Ajouter les avertissements de validation si présents
        warnings = ""
        if params["errors"]:
            warnings = "⚠️ " + " | ".join(params["errors"]) + "\n\n"

        response = formater_resultats_rss(result["articles"], result["categories"])
        return [TextContent(type="text", text=warnings + response)]
    
    # --- Analyse Claude ---
    elif name == "analyser_resultats":
        if not derniers_resultats["data"]:
            return [TextContent(type="text", text="❌ Aucun résultat à analyser. Lancez d'abord une recherche ou une veille.")]
        
        result = analyser_avec_claude(derniers_resultats["data"], derniers_resultats["query"])
        
        if not result["success"]:
            return [TextContent(type="text", text=f"❌ Erreur: {result['error']}")]
        
        response = f"🤖 **Analyse Claude** ({result['nb_articles_analyses']} articles)\n\n{result['analyse']}"
        return [TextContent(type="text", text=response)]
    
    # --- Générer rapport ---
    elif name == "generer_rapport":
        result = generer_rapport(inclure_analyse=arguments.get("inclure_analyse", True))
        
        if not result["success"]:
            return [TextContent(type="text", text=f"❌ {result['error']}")]
        
        response_lines = [
            f"📄 **Rapport généré** (ID: {result['rapport_id']})",
            f"📊 {result['nb_articles']} articles inclus",
            "",
            "---",
            result["contenu"][:2000],  # Limiter l'affichage
        ]
        
        if result["analyse"]:
            response_lines.extend([
                "",
                "---",
                "🤖 **Analyse:**",
                result["analyse"]
            ])
        
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    # --- Favoris ---
    elif name == "ajouter_favori":
        result = ajouter_favori(
            url=arguments.get("url", ""),
            titre=arguments.get("titre", ""),
            source=arguments.get("source", ""),
            description=arguments.get("description", ""),
            tags=arguments.get("tags", "")
        )
        
        if result["success"]:
            return [TextContent(type="text", text=f"✅ Article ajouté aux favoris (ID: {result['favori_id']})")]
        return [TextContent(type="text", text=f"⚠️ {result['error']}")]
    
    elif name == "lister_favoris":
        result = lister_favoris(arguments.get("limite", 20))
        
        if not result["success"]:
            return [TextContent(type="text", text=f"❌ {result['error']}")]
        
        if not result["favoris"]:
            return [TextContent(type="text", text="📭 Aucun favori enregistré.")]
        
        lines = [f"📚 **Vos Favoris** ({len(result['favoris'])}/{result['total']})\n"]
        for fav in result["favoris"]:
            lines.append(f"**{fav['id']}. {fav['titre']}**")
            lines.append(f"   📰 {fav['source'] or 'N/A'} | 📅 {fav['date_ajout'][:10]}")
            lines.append(f"   🔗 {fav['url']}")
            lines.append("")
        
        return [TextContent(type="text", text="\n".join(lines))]
    
    elif name == "supprimer_favori":
        result = supprimer_favori(arguments.get("favori_id"), arguments.get("url"))
        
        if result["success"]:
            return [TextContent(type="text", text="✅ Favori supprimé.")]
        return [TextContent(type="text", text=f"❌ {result['error']}")]
    
    else:
        return [TextContent(type="text", text=f"❌ Outil '{name}' non reconnu.")]


# =============================================================================
# FONCTIONS DE FORMATAGE
# =============================================================================

def formater_resultats_recherche(articles: list, titre: str) -> str:
    """Formate les résultats de recherche pour l'affichage."""
    lines = [
        f"🔍 **{titre}**",
        f"📊 {len(articles)} articles trouvés",
        "",
        "---",
        ""
    ]
    
    for i, art in enumerate(articles, 1):
        lines.append(f"**{i}. {art.get('titre', 'N/A')}**")
        date_str = art.get('date', '')[:10] if art.get('date') else 'N/A'
        lines.append(f"   📰 {art.get('source', 'N/A')} | 📅 {date_str}")
        lines.append(f"   🔗 {art.get('url', 'N/A')}")
        if art.get('description'):
            lines.append(f"   💬 {art['description']}")
        lines.append("")
    
    lines.append("---")
    lines.append("💡 *Utilisez 'analyser_resultats' pour une synthèse IA, ou 'ajouter_favori' pour sauvegarder.*")
    
    return "\n".join(lines)


def formater_resultats_rss(articles: list, categories: list) -> str:
    """Formate les résultats RSS pour l'affichage."""
    lines = [
        "📡 **Veille RSS**",
        f"📂 Catégories: {', '.join(categories)}",
        f"📊 {len(articles)} articles collectés",
        "",
        "---",
        ""
    ]
    
    # Grouper par catégorie
    by_cat = {}
    for art in articles:
        cat = art.get('categorie_rss', 'Autre')
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(art)
    
    for cat, arts in by_cat.items():
        lines.append(f"**📂 {cat}** ({len(arts)} articles)")
        lines.append("")
        
        for i, art in enumerate(arts[:5], 1):  # Max 5 par catégorie
            lines.append(f"  {i}. **{art.get('titre', 'N/A')}**")
            lines.append(f"     📰 {art.get('source', 'N/A')}")
            lines.append(f"     🔗 {art.get('url', 'N/A')}")
            lines.append("")
        
        if len(arts) > 5:
            lines.append(f"  *... et {len(arts) - 5} autres articles*")
            lines.append("")
    
    lines.append("---")
    lines.append("💡 *Utilisez 'analyser_resultats' pour une synthèse IA.*")
    
    return "\n".join(lines)


# =============================================================================
# RESSOURCES MCP
# =============================================================================

@server.list_resources()
async def list_resources() -> list[Resource]:
    """Déclare les ressources MCP disponibles."""
    return [
        Resource(uri="veille://favoris", name="Favoris", description="Articles favoris", mimeType="application/json"),
        Resource(uri="veille://thematiques", name="Thématiques", description="Liste des thématiques", mimeType="application/json"),
        Resource(uri="veille://historique", name="Historique", description="Historique des recherches", mimeType="application/json"),
        Resource(uri="veille://rss-feeds", name="Flux RSS", description="Configuration des flux RSS", mimeType="application/json"),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Lit une ressource MCP."""
    
    if uri == "veille://favoris":
        result = lister_favoris(100)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    elif uri == "veille://thematiques":
        return json.dumps(THEMATIQUES, ensure_ascii=False, indent=2)
    
    elif uri == "veille://rss-feeds":
        return json.dumps(RSS_FEEDS, ensure_ascii=False, indent=2)
    
    elif uri == "veille://historique":
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT type, query, date_recherche, nb_resultats
                    FROM historique_recherches
                    ORDER BY date_recherche DESC LIMIT 50
                """)
                historique = [dict(row) for row in cursor.fetchall()]
                return json.dumps({"historique": historique}, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erreur lecture historique ressource: {e}")
            return json.dumps({"historique": [], "error": str(e)})
    
    return json.dumps({"error": f"Ressource inconnue: {uri}"})


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

async def main():
    """Démarre le serveur MCP."""
    
    logger.info("=" * 60)
    logger.info("🚀 MCP Veille V3 - Phase 3")
    logger.info("=" * 60)
    
    init_database()
    
    if NEWS_API_KEY:
        logger.info("✅ NEWS_API_KEY configurée")
    else:
        logger.warning("⚠️ NEWS_API_KEY manquante")
    
    if ANTHROPIC_API_KEY:
        logger.info("✅ ANTHROPIC_API_KEY configurée")
    else:
        logger.warning("⚠️ ANTHROPIC_API_KEY manquante (analyse désactivée)")
    
    logger.info(f"📁 Base de données: {DB_PATH}")
    logger.info(f"🎯 Thématiques: {len(THEMATIQUES)}")
    logger.info(f"📡 Flux RSS: {sum(len(feeds) for feeds in RSS_FEEDS.values())}")
    logger.info("📡 En attente de connexions...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())