#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Veille V3 - Serveur Principal
=================================

Ce serveur MCP permet d'interagir avec un système de veille technologique
directement depuis Claude Desktop en langage naturel.

Phase 1 : Socle minimal pour valider la connexion Claude Desktop
- 1 outil : rechercher_actualites (recherche via NewsAPI)
- Objectif : confirmer que la chaîne technique fonctionne

Utilisation :
    Ce script est lancé automatiquement par Claude Desktop via la config JSON.
    Il communique via stdin/stdout avec le protocole MCP.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Any

# Import du SDK MCP
# Le SDK gère toute la communication avec Claude Desktop
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import pour les appels API
import requests
from dotenv import load_dotenv

# =============================================================================
# CONFIGURATION
# =============================================================================

# Charger les variables d'environnement depuis .env
# Le fichier .env doit être dans le même répertoire que ce script ou à la racine du projet
load_dotenv()

# Récupérer les clés API
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Configuration du logging pour le debug
# Les logs vont dans stderr pour ne pas interférer avec la communication MCP (qui utilise stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("veille-mcp")

# =============================================================================
# CRÉATION DU SERVEUR MCP
# =============================================================================

# Le serveur MCP est l'objet central qui gère tous les outils, ressources et prompts
# Le nom "veille-system" sera visible dans Claude Desktop
server = Server("veille-system")

# =============================================================================
# FONCTIONS MÉTIER
# =============================================================================

def rechercher_newsapi(query: str, jours: int = 7, max_resultats: int = 10) -> dict:
    """
    Recherche des articles via l'API NewsAPI.
    
    Cette fonction fait le vrai travail de recherche. Elle est séparée de l'outil MCP
    pour faciliter les tests et la maintenance.
    
    Args:
        query: Les mots-clés de recherche (ex: "Claude Anthropic AI")
        jours: Nombre de jours dans le passé à couvrir
        max_resultats: Nombre maximum d'articles à retourner
    
    Returns:
        Un dictionnaire avec le statut et les articles trouvés
    """
    
    # Vérifier que la clé API est configurée
    if not NEWS_API_KEY:
        logger.error("NEWS_API_KEY non configurée dans .env")
        return {
            "success": False,
            "error": "Clé API NewsAPI non configurée. Vérifiez votre fichier .env",
            "articles": []
        }
    
    try:
        # Calculer la date de début de recherche
        date_debut = (datetime.now() - timedelta(days=jours)).strftime("%Y-%m-%d")
        
        # Construire la requête vers NewsAPI
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": date_debut,
            "sortBy": "publishedAt",  # Plus récents en premier
            "language": "en",          # Articles en anglais (fr limité sur NewsAPI gratuit)
            "pageSize": min(max_resultats, 100),  # NewsAPI limite à 100
            "apiKey": NEWS_API_KEY
        }
        
        logger.info(f"Recherche NewsAPI: '{query}' sur {jours} jours")
        
        # Effectuer la requête
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Vérifier le statut de la réponse NewsAPI
        if data.get("status") != "ok":
            error_msg = data.get("message", "Erreur inconnue NewsAPI")
            logger.error(f"Erreur NewsAPI: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "articles": []
            }
        
        # Extraire et formater les articles
        articles_raw = data.get("articles", [])
        articles = []
        
        for art in articles_raw:
            # Extraire le nom de la source (peut être un dict ou une string)
            source = art.get("source", {})
            source_name = source.get("name", "Source inconnue") if isinstance(source, dict) else str(source)
            
            # Construire l'article formaté
            article = {
                "titre": art.get("title", "Sans titre"),
                "source": source_name,
                "date": art.get("publishedAt", "Date inconnue"),
                "url": art.get("url", ""),
                "description": art.get("description", "")[:200] if art.get("description") else ""
            }
            articles.append(article)
        
        logger.info(f"Trouvé {len(articles)} articles pour '{query}'")
        
        return {
            "success": True,
            "query": query,
            "periode_jours": jours,
            "total_articles": len(articles),
            "articles": articles
        }
        
    except requests.exceptions.Timeout:
        logger.error("Timeout lors de la requête NewsAPI")
        return {
            "success": False,
            "error": "La requête a pris trop de temps. Réessayez.",
            "articles": []
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur réseau NewsAPI: {e}")
        return {
            "success": False,
            "error": f"Erreur de connexion: {str(e)}",
            "articles": []
        }
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return {
            "success": False,
            "error": f"Erreur inattendue: {str(e)}",
            "articles": []
        }


# =============================================================================
# OUTILS MCP
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    Déclare les outils disponibles dans ce serveur MCP.
    
    Cette fonction est appelée par Claude Desktop au démarrage pour savoir
    quels outils sont disponibles. Chaque outil a :
    - Un nom unique (utilisé pour l'appeler)
    - Une description (aide Claude à comprendre quand l'utiliser)
    - Un schéma JSON des paramètres attendus
    
    Pour la Phase 1, on n'a qu'un seul outil simple.
    """
    
    return [
        Tool(
            name="rechercher_actualites",
            description="""Recherche des actualités technologiques récentes sur un sujet donné.
            
Utilise cet outil quand l'utilisateur veut :
- Chercher des news sur un sujet tech (IA, Claude, OpenAI, etc.)
- Faire une veille sur une thématique
- Trouver des articles récents

Exemples de requêtes utilisateur :
- "Cherche des news sur Claude et Anthropic"
- "Quelles sont les dernières actualités sur l'IA ?"
- "Lance une veille sur GPT-5"
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
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Exécute un outil MCP quand Claude Desktop le demande.
    
    Cette fonction est appelée automatiquement quand Claude décide d'utiliser
    un de nos outils. Elle reçoit le nom de l'outil et ses arguments.
    
    Args:
        name: Le nom de l'outil à exécuter
        arguments: Les paramètres passés à l'outil (dict)
    
    Returns:
        Une liste de TextContent avec le résultat (format MCP)
    """
    
    logger.info(f"Appel outil: {name} avec arguments: {arguments}")
    
    if name == "rechercher_actualites":
        # Extraire les paramètres avec valeurs par défaut
        sujet = arguments.get("sujet", "")
        jours = arguments.get("jours", 7)
        max_articles = arguments.get("max_articles", 10)
        
        # Valider le sujet
        if not sujet:
            return [TextContent(
                type="text",
                text="❌ Erreur : veuillez spécifier un sujet de recherche."
            )]
        
        # Effectuer la recherche
        resultat = rechercher_newsapi(sujet, jours, max_articles)
        
        # Formater la réponse pour Claude
        if not resultat["success"]:
            return [TextContent(
                type="text",
                text=f"❌ Erreur lors de la recherche : {resultat['error']}"
            )]
        
        # Construire une réponse lisible
        articles = resultat["articles"]
        
        if not articles:
            response_text = f"🔍 Aucun article trouvé pour '{sujet}' sur les {jours} derniers jours."
        else:
            # En-tête du résultat
            response_lines = [
                f"🔍 **Recherche : {sujet}**",
                f"📅 Période : {jours} derniers jours",
                f"📊 Résultats : {len(articles)} articles",
                "",
                "---",
                ""
            ]
            
            # Liste des articles
            for i, art in enumerate(articles, 1):
                response_lines.append(f"**{i}. {art['titre']}**")
                response_lines.append(f"   📰 {art['source']} | 📅 {art['date'][:10] if art['date'] else 'N/A'}")
                response_lines.append(f"   🔗 {art['url']}")
                if art['description']:
                    response_lines.append(f"   💬 {art['description']}")
                response_lines.append("")
            
            response_text = "\n".join(response_lines)
        
        return [TextContent(
            type="text",
            text=response_text
        )]
    
    else:
        # Outil non reconnu
        logger.warning(f"Outil inconnu demandé: {name}")
        return [TextContent(
            type="text",
            text=f"❌ Outil '{name}' non reconnu."
        )]


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

async def main():
    """
    Démarre le serveur MCP.
    
    Le serveur utilise stdio (stdin/stdout) pour communiquer avec Claude Desktop.
    C'est le mode standard pour les serveurs MCP locaux.
    """
    
    logger.info("=" * 60)
    logger.info("🚀 Démarrage du serveur MCP Veille V3")
    logger.info("=" * 60)
    
    # Vérifier la configuration
    if NEWS_API_KEY:
        logger.info("✅ NEWS_API_KEY configurée")
    else:
        logger.warning("⚠️ NEWS_API_KEY non configurée - les recherches échoueront")
    
    logger.info("📡 En attente de connexions Claude Desktop...")
    
    # Démarrer le serveur en mode stdio
    # Cette fonction bloque et gère toute la communication MCP
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
