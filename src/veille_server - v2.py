#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Veille V3 - Serveur Principal
=================================

Phase 2 : État persistant avec SQLite
- Base de données pour favoris, historique, rapports
- Outils : rechercher_actualites, ajouter_favori, lister_favoris, supprimer_favori
- Ressources : veille://favoris, veille://historique

Utilisation :
    Ce script est lancé automatiquement par Claude Desktop via la config JSON.
    Il communique via stdin/stdout avec le protocole MCP.
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from contextlib import contextmanager

# Import du SDK MCP
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

# Import pour les appels API
import requests
from dotenv import load_dotenv

# =============================================================================
# CONFIGURATION
# =============================================================================

# Déterminer le répertoire du projet (parent du dossier src)
PROJECT_DIR = Path(__file__).parent.parent

# Charger les variables d'environnement depuis .env à la racine du projet
load_dotenv(PROJECT_DIR / ".env")

# Récupérer les clés API
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Chemin de la base de données SQLite
DB_PATH = PROJECT_DIR / "data" / "veille.db"

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("veille-mcp")

# =============================================================================
# BASE DE DONNÉES SQLITE
# =============================================================================

def init_database():
    """
    Initialise la base de données SQLite avec les tables nécessaires.
    
    Cette fonction est appelée au démarrage du serveur. Elle crée les tables
    si elles n'existent pas encore, ce qui permet un démarrage propre même
    si la base n'existe pas.
    """
    
    # S'assurer que le dossier data existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initialisation de la base de données: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table des favoris
    # Stocke les articles que l'utilisateur souhaite garder
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favoris (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            titre TEXT NOT NULL,
            source TEXT,
            description TEXT,
            date_article TEXT,
            date_ajout TEXT NOT NULL,
            tags TEXT
        )
    """)
    
    # Table de l'historique des recherches
    # Permet de voir les recherches passées et leurs résultats
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historique_recherches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            date_recherche TEXT NOT NULL,
            nb_resultats INTEGER,
            parametres TEXT
        )
    """)
    
    # Table des rapports générés (pour Phase 3)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rapports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            date_creation TEXT NOT NULL,
            contenu TEXT,
            metadata TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    
    logger.info("Base de données initialisée avec succès")


@contextmanager
def get_db_connection():
    """
    Context manager pour les connexions à la base de données.
    
    Utilisation:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    
    Garantit que la connexion est fermée même en cas d'erreur.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    try:
        yield conn
    finally:
        conn.close()


# =============================================================================
# CRÉATION DU SERVEUR MCP
# =============================================================================

server = Server("veille-system")

# =============================================================================
# FONCTIONS MÉTIER - RECHERCHE
# =============================================================================

def rechercher_newsapi(query: str, jours: int = 7, max_resultats: int = 10) -> dict:
    """
    Recherche des articles via l'API NewsAPI.
    
    Args:
        query: Les mots-clés de recherche
        jours: Nombre de jours dans le passé à couvrir
        max_resultats: Nombre maximum d'articles à retourner
    
    Returns:
        Un dictionnaire avec le statut et les articles trouvés
    """
    
    if not NEWS_API_KEY:
        logger.error("NEWS_API_KEY non configurée dans .env")
        return {
            "success": False,
            "error": "Clé API NewsAPI non configurée. Vérifiez votre fichier .env",
            "articles": []
        }
    
    try:
        date_debut = (datetime.now() - timedelta(days=jours)).strftime("%Y-%m-%d")
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": date_debut,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": min(max_resultats, 100),
            "apiKey": NEWS_API_KEY
        }
        
        logger.info(f"Recherche NewsAPI: '{query}' sur {jours} jours")
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") != "ok":
            error_msg = data.get("message", "Erreur inconnue NewsAPI")
            logger.error(f"Erreur NewsAPI: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "articles": []
            }
        
        articles_raw = data.get("articles", [])
        articles = []
        
        for art in articles_raw:
            source = art.get("source", {})
            source_name = source.get("name", "Source inconnue") if isinstance(source, dict) else str(source)
            
            article = {
                "titre": art.get("title", "Sans titre"),
                "source": source_name,
                "date": art.get("publishedAt", "Date inconnue"),
                "url": art.get("url", ""),
                "description": art.get("description", "")[:200] if art.get("description") else ""
            }
            articles.append(article)
        
        logger.info(f"Trouvé {len(articles)} articles pour '{query}'")
        
        # Enregistrer dans l'historique
        enregistrer_recherche(query, len(articles), {"jours": jours, "max": max_resultats})
        
        return {
            "success": True,
            "query": query,
            "periode_jours": jours,
            "total_articles": len(articles),
            "articles": articles
        }
        
    except requests.exceptions.Timeout:
        logger.error("Timeout lors de la requête NewsAPI")
        return {"success": False, "error": "La requête a pris trop de temps.", "articles": []}
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur réseau NewsAPI: {e}")
        return {"success": False, "error": f"Erreur de connexion: {str(e)}", "articles": []}
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return {"success": False, "error": f"Erreur inattendue: {str(e)}", "articles": []}


def enregistrer_recherche(query: str, nb_resultats: int, parametres: dict):
    """Enregistre une recherche dans l'historique."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historique_recherches (query, date_recherche, nb_resultats, parametres)
                VALUES (?, ?, ?, ?)
            """, (query, datetime.now().isoformat(), nb_resultats, json.dumps(parametres)))
            conn.commit()
    except Exception as e:
        logger.error(f"Erreur enregistrement historique: {e}")


# =============================================================================
# FONCTIONS MÉTIER - FAVORIS
# =============================================================================

def ajouter_favori(url: str, titre: str, source: str = "", description: str = "", date_article: str = "", tags: str = "") -> dict:
    """
    Ajoute un article aux favoris.
    
    Args:
        url: URL unique de l'article
        titre: Titre de l'article
        source: Nom de la source (optionnel)
        description: Description courte (optionnel)
        date_article: Date de publication (optionnel)
        tags: Tags séparés par des virgules (optionnel)
    
    Returns:
        Dictionnaire avec le statut de l'opération
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Vérifier si l'article existe déjà
            cursor.execute("SELECT id FROM favoris WHERE url = ?", (url,))
            existing = cursor.fetchone()
            
            if existing:
                return {
                    "success": False,
                    "error": "Cet article est déjà dans vos favoris",
                    "favori_id": existing["id"]
                }
            
            # Insérer le nouveau favori
            cursor.execute("""
                INSERT INTO favoris (url, titre, source, description, date_article, date_ajout, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (url, titre, source, description, date_article, datetime.now().isoformat(), tags))
            
            conn.commit()
            favori_id = cursor.lastrowid
            
            logger.info(f"Favori ajouté: {titre[:50]}... (ID: {favori_id})")
            
            return {
                "success": True,
                "message": "Article ajouté aux favoris",
                "favori_id": favori_id
            }
            
    except Exception as e:
        logger.error(f"Erreur ajout favori: {e}")
        return {"success": False, "error": str(e)}


def lister_favoris(limite: int = 20) -> dict:
    """
    Liste les favoris enregistrés.
    
    Args:
        limite: Nombre maximum de favoris à retourner
    
    Returns:
        Dictionnaire avec la liste des favoris
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, url, titre, source, description, date_article, date_ajout, tags
                FROM favoris
                ORDER BY date_ajout DESC
                LIMIT ?
            """, (limite,))
            
            rows = cursor.fetchall()
            
            favoris = []
            for row in rows:
                favoris.append({
                    "id": row["id"],
                    "url": row["url"],
                    "titre": row["titre"],
                    "source": row["source"] or "N/A",
                    "description": row["description"] or "",
                    "date_article": row["date_article"] or "N/A",
                    "date_ajout": row["date_ajout"],
                    "tags": row["tags"] or ""
                })
            
            # Compter le total
            cursor.execute("SELECT COUNT(*) FROM favoris")
            total = cursor.fetchone()[0]
            
            return {
                "success": True,
                "favoris": favoris,
                "total": total,
                "affichés": len(favoris)
            }
            
    except Exception as e:
        logger.error(f"Erreur listage favoris: {e}")
        return {"success": False, "error": str(e), "favoris": []}


def supprimer_favori(favori_id: int = None, url: str = None) -> dict:
    """
    Supprime un favori par ID ou par URL.
    
    Args:
        favori_id: ID du favori à supprimer
        url: URL de l'article à supprimer
    
    Returns:
        Dictionnaire avec le statut de l'opération
    """
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
                logger.info(f"Favori supprimé (ID: {favori_id}, URL: {url})")
                return {"success": True, "message": "Favori supprimé"}
            else:
                return {"success": False, "error": "Favori non trouvé"}
                
    except Exception as e:
        logger.error(f"Erreur suppression favori: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# OUTILS MCP
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    Déclare les outils disponibles dans ce serveur MCP.
    
    Phase 2 : 4 outils disponibles
    - rechercher_actualites : Recherche d'articles
    - ajouter_favori : Sauvegarder un article
    - lister_favoris : Voir les favoris
    - supprimer_favori : Retirer un favori
    """
    
    return [
        Tool(
            name="rechercher_actualites",
            description="""Recherche des actualités technologiques récentes sur un sujet donné.
            
Utilise cet outil quand l'utilisateur veut :
- Chercher des news sur un sujet tech (IA, Claude, OpenAI, etc.)
- Faire une veille sur une thématique
- Trouver des articles récents

Exemples : "Cherche des news sur Claude", "Actualités IA cette semaine"
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "sujet": {
                        "type": "string",
                        "description": "Le sujet de recherche (mots-clés)"
                    },
                    "jours": {
                        "type": "integer",
                        "description": "Nombre de jours à couvrir (défaut: 7)",
                        "default": 7
                    },
                    "max_articles": {
                        "type": "integer",
                        "description": "Nombre maximum d'articles (défaut: 10)",
                        "default": 10
                    }
                },
                "required": ["sujet"]
            }
        ),
        
        Tool(
            name="ajouter_favori",
            description="""Ajoute un article aux favoris de l'utilisateur.
            
Utilise cet outil quand l'utilisateur veut :
- Sauvegarder un article pour plus tard
- Marquer un article comme important
- Garder un article en favori

Exemples : "Garde cet article", "Ajoute le premier à mes favoris", "Sauvegarde cet article"
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL de l'article"
                    },
                    "titre": {
                        "type": "string",
                        "description": "Titre de l'article"
                    },
                    "source": {
                        "type": "string",
                        "description": "Nom de la source (optionnel)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description courte (optionnel)"
                    },
                    "date_article": {
                        "type": "string",
                        "description": "Date de publication (optionnel)"
                    },
                    "tags": {
                        "type": "string",
                        "description": "Tags séparés par virgules (optionnel)"
                    }
                },
                "required": ["url", "titre"]
            }
        ),
        
        Tool(
            name="lister_favoris",
            description="""Liste les articles favoris de l'utilisateur.
            
Utilise cet outil quand l'utilisateur veut :
- Voir ses favoris
- Consulter les articles sauvegardés
- Retrouver un article gardé

Exemples : "Montre mes favoris", "Quels articles j'ai sauvegardés ?", "Liste mes favoris"
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limite": {
                        "type": "integer",
                        "description": "Nombre maximum de favoris à afficher (défaut: 20)",
                        "default": 20
                    }
                }
            }
        ),
        
        Tool(
            name="supprimer_favori",
            description="""Supprime un article des favoris.
            
Utilise cet outil quand l'utilisateur veut :
- Retirer un article des favoris
- Supprimer un favori
- Enlever un article sauvegardé

Exemples : "Retire le favori 3", "Supprime cet article de mes favoris"
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "favori_id": {
                        "type": "integer",
                        "description": "ID du favori à supprimer"
                    },
                    "url": {
                        "type": "string",
                        "description": "URL de l'article à supprimer (alternative à l'ID)"
                    }
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Exécute un outil MCP quand Claude Desktop le demande.
    """
    
    logger.info(f"Appel outil: {name} avec arguments: {arguments}")
    
    if name == "rechercher_actualites":
        sujet = arguments.get("sujet", "")
        jours = arguments.get("jours", 7)
        max_articles = arguments.get("max_articles", 10)
        
        if not sujet:
            return [TextContent(type="text", text="❌ Erreur : veuillez spécifier un sujet de recherche.")]
        
        resultat = rechercher_newsapi(sujet, jours, max_articles)
        
        if not resultat["success"]:
            return [TextContent(type="text", text=f"❌ Erreur : {resultat['error']}")]
        
        articles = resultat["articles"]
        
        if not articles:
            return [TextContent(type="text", text=f"🔍 Aucun article trouvé pour '{sujet}' sur les {jours} derniers jours.")]
        
        response_lines = [
            f"🔍 **Recherche : {sujet}**",
            f"📅 Période : {jours} derniers jours",
            f"📊 Résultats : {len(articles)} articles",
            "",
            "---",
            ""
        ]
        
        for i, art in enumerate(articles, 1):
            response_lines.append(f"**{i}. {art['titre']}**")
            response_lines.append(f"   📰 {art['source']} | 📅 {art['date'][:10] if art['date'] else 'N/A'}")
            response_lines.append(f"   🔗 {art['url']}")
            if art['description']:
                response_lines.append(f"   💬 {art['description']}")
            response_lines.append("")
        
        response_lines.append("---")
        response_lines.append("💡 *Tu peux me demander d'ajouter un article à tes favoris !*")
        
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    elif name == "ajouter_favori":
        url = arguments.get("url", "")
        titre = arguments.get("titre", "")
        
        if not url or not titre:
            return [TextContent(type="text", text="❌ Erreur : URL et titre sont requis.")]
        
        resultat = ajouter_favori(
            url=url,
            titre=titre,
            source=arguments.get("source", ""),
            description=arguments.get("description", ""),
            date_article=arguments.get("date_article", ""),
            tags=arguments.get("tags", "")
        )
        
        if resultat["success"]:
            return [TextContent(type="text", text=f"✅ Article ajouté aux favoris !\n\n📌 **{titre}**\n🔗 {url}\n\n*ID du favori : {resultat['favori_id']}*")]
        else:
            return [TextContent(type="text", text=f"⚠️ {resultat['error']}")]
    
    elif name == "lister_favoris":
        limite = arguments.get("limite", 20)
        
        resultat = lister_favoris(limite)
        
        if not resultat["success"]:
            return [TextContent(type="text", text=f"❌ Erreur : {resultat['error']}")]
        
        favoris = resultat["favoris"]
        
        if not favoris:
            return [TextContent(type="text", text="📭 Vous n'avez pas encore de favoris.\n\n*Faites une recherche et demandez-moi d'ajouter des articles !*")]
        
        response_lines = [
            f"📚 **Vos Favoris** ({resultat['affichés']}/{resultat['total']})",
            "",
            "---",
            ""
        ]
        
        for fav in favoris:
            response_lines.append(f"**{fav['id']}. {fav['titre']}**")
            response_lines.append(f"   📰 {fav['source']} | 📅 Ajouté le {fav['date_ajout'][:10]}")
            response_lines.append(f"   🔗 {fav['url']}")
            if fav['tags']:
                response_lines.append(f"   🏷️ {fav['tags']}")
            response_lines.append("")
        
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    elif name == "supprimer_favori":
        favori_id = arguments.get("favori_id")
        url = arguments.get("url")
        
        resultat = supprimer_favori(favori_id=favori_id, url=url)
        
        if resultat["success"]:
            return [TextContent(type="text", text="✅ Favori supprimé avec succès.")]
        else:
            return [TextContent(type="text", text=f"❌ Erreur : {resultat['error']}")]
    
    else:
        logger.warning(f"Outil inconnu: {name}")
        return [TextContent(type="text", text=f"❌ Outil '{name}' non reconnu.")]


# =============================================================================
# RESSOURCES MCP
# =============================================================================

@server.list_resources()
async def list_resources() -> list[Resource]:
    """
    Déclare les ressources disponibles dans ce serveur MCP.
    
    Les ressources sont des données que Claude peut lire directement,
    sans avoir besoin d'appeler un outil.
    """
    
    return [
        Resource(
            uri="veille://favoris",
            name="Liste des favoris",
            description="Tous les articles favoris de l'utilisateur au format JSON",
            mimeType="application/json"
        ),
        Resource(
            uri="veille://historique",
            name="Historique des recherches",
            description="Les dernières recherches effectuées",
            mimeType="application/json"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """
    Lit le contenu d'une ressource MCP.
    
    Args:
        uri: URI de la ressource à lire (ex: veille://favoris)
    
    Returns:
        Contenu de la ressource (généralement du JSON)
    """
    
    logger.info(f"Lecture ressource: {uri}")
    
    if uri == "veille://favoris":
        resultat = lister_favoris(limite=100)
        return json.dumps(resultat, ensure_ascii=False, indent=2)
    
    elif uri == "veille://historique":
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT query, date_recherche, nb_resultats, parametres
                    FROM historique_recherches
                    ORDER BY date_recherche DESC
                    LIMIT 50
                """)
                rows = cursor.fetchall()
                
                historique = []
                for row in rows:
                    historique.append({
                        "query": row["query"],
                        "date": row["date_recherche"],
                        "nb_resultats": row["nb_resultats"],
                        "parametres": json.loads(row["parametres"]) if row["parametres"] else {}
                    })
                
                return json.dumps({"historique": historique}, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    else:
        return json.dumps({"error": f"Ressource inconnue: {uri}"})


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

async def main():
    """
    Démarre le serveur MCP.
    """
    
    logger.info("=" * 60)
    logger.info("🚀 Démarrage du serveur MCP Veille V3 - Phase 2")
    logger.info("=" * 60)
    
    # Initialiser la base de données
    init_database()
    
    # Vérifier la configuration
    if NEWS_API_KEY:
        logger.info("✅ NEWS_API_KEY configurée")
    else:
        logger.warning("⚠️ NEWS_API_KEY non configurée")
    
    logger.info(f"📁 Base de données: {DB_PATH}")
    logger.info("📡 En attente de connexions Claude Desktop...")
    
    # Démarrer le serveur
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
