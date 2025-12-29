#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du Serveur MCP Veille V3
=============================

Ce script teste le serveur MCP en isolation, SANS Claude Desktop.
Il permet de vérifier que :
1. Les imports fonctionnent
2. Les clés API sont configurées
3. La recherche NewsAPI fonctionne
4. Le serveur MCP peut être initialisé

Utilisation :
    python tests/test_server.py
"""

import os
import sys

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def print_header(title: str):
    """Affiche un en-tête formaté."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_imports():
    """Teste que tous les imports nécessaires fonctionnent."""
    print_header("TEST 1: Imports")
    
    try:
        import mcp
        print(f"  ✅ mcp importé (version: {getattr(mcp, '__version__', 'inconnue')})")
    except ImportError as e:
        print(f"  ❌ Erreur import mcp: {e}")
        print("     → Installer avec: pip install mcp")
        return False
    
    try:
        import requests
        print(f"  ✅ requests importé")
    except ImportError as e:
        print(f"  ❌ Erreur import requests: {e}")
        return False
    
    try:
        from veille_server import rechercher_newsapi, server
        print(f"  ✅ veille_server importé")
    except ImportError as e:
        print(f"  ❌ Erreur import veille_server: {e}")
        return False
    
    return True


def test_configuration():
    """Teste que les clés API sont configurées."""
    print_header("TEST 2: Configuration")
    
    news_api_key = os.getenv("NEWS_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if news_api_key:
        # Masquer la clé pour l'affichage
        masked = news_api_key[:8] + "..." + news_api_key[-4:] if len(news_api_key) > 12 else "***"
        print(f"  ✅ NEWS_API_KEY configurée ({masked})")
    else:
        print("  ❌ NEWS_API_KEY non configurée")
        print("     → Créez un fichier .env avec votre clé")
        return False
    
    if anthropic_key:
        masked = anthropic_key[:8] + "..." + anthropic_key[-4:] if len(anthropic_key) > 12 else "***"
        print(f"  ✅ ANTHROPIC_API_KEY configurée ({masked})")
    else:
        print("  ⚠️  ANTHROPIC_API_KEY non configurée (optionnel pour Phase 1)")
    
    return True


def test_newsapi():
    """Teste une vraie recherche NewsAPI."""
    print_header("TEST 3: Recherche NewsAPI")
    
    from veille_server import rechercher_newsapi
    
    print("  🔍 Recherche: 'artificial intelligence' (3 jours, max 3 articles)")
    
    resultat = rechercher_newsapi("artificial intelligence", jours=3, max_resultats=3)
    
    if resultat["success"]:
        print(f"  ✅ Recherche réussie: {resultat['total_articles']} articles trouvés")
        
        if resultat["articles"]:
            print("\n  📰 Aperçu des articles:")
            for i, art in enumerate(resultat["articles"][:3], 1):
                titre = art["titre"][:50] + "..." if len(art["titre"]) > 50 else art["titre"]
                print(f"     {i}. {titre}")
                print(f"        Source: {art['source']}")
        
        return True
    else:
        print(f"  ❌ Erreur: {resultat['error']}")
        return False


def test_mcp_server():
    """Teste l'initialisation du serveur MCP."""
    print_header("TEST 4: Serveur MCP")
    
    try:
        from veille_server import server
        
        print(f"  ✅ Serveur MCP créé: {server.name}")
        print(f"  ✅ Le serveur est prêt à être connecté à Claude Desktop")
        
        return True
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False


def main():
    """Exécute tous les tests."""
    print("\n" + "=" * 60)
    print("  🧪 TESTS DU SERVEUR MCP VEILLE V3")
    print("=" * 60)
    
    # Compteurs
    tests_ok = 0
    tests_total = 0
    
    # Test 1: Imports
    tests_total += 1
    if test_imports():
        tests_ok += 1
    
    # Test 2: Configuration
    tests_total += 1
    if test_configuration():
        tests_ok += 1
    else:
        print("\n  ⚠️  Configuration incomplète, tests suivants ignorés")
        print_summary(tests_ok, tests_total)
        return
    
    # Test 3: NewsAPI
    tests_total += 1
    if test_newsapi():
        tests_ok += 1
    
    # Test 4: Serveur MCP
    tests_total += 1
    if test_mcp_server():
        tests_ok += 1
    
    # Résumé
    print_summary(tests_ok, tests_total)


def print_summary(ok: int, total: int):
    """Affiche le résumé des tests."""
    print_header("RÉSUMÉ")
    
    if ok == total:
        print(f"  ✅ TOUS LES TESTS RÉUSSIS ({ok}/{total})")
        print("\n  🚀 Prochaine étape: Configurer Claude Desktop")
        print("     Voir le fichier README.md pour les instructions")
    else:
        print(f"  ⚠️  {ok}/{total} tests réussis")
        print("\n  📋 Corrigez les erreurs avant de continuer")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
