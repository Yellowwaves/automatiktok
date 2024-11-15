# Utilisation des scripts

Ce dossier contient plusieurs scripts Python et Bash. Voici leur utilisation :

## `setup_script.py`
Ce script gère toute la configuration de base et crée une première BDD fonctionnelle ainsi qu'une interface web pour la visualiser. Il est nécessaire de lancer ce script en premier.

## `ids_server_full.sh`
Ce script lance le serveur IDS complet avec l'installation de Snort et d'Apache pour visualiser les alertes. Il faut le lancer sur le serveur web après avoir exécuté le script Python.

## Autres scripts
Tous les autres scripts sont inutiles, ils sont là pour des tests et des démonstrations.

# Utilisation de l'interface web

## Partie 1 : Connexion bdd et PHP

Le site sera présent sur l'adresse IP (http) du serveur web sur le port 80 
`http://votre_ip/`

## Partie 2 : interface IDS

L'interface Snort sera accessible sur l'adresse IP (http) du serveur web sur le port 80
`http://votre_ip/flask`