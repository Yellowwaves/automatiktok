#!/bin/bash
 
# Mise à jour du système
sudo apt update
 
# Installation des dépendances
sudo apt install -y snort tcpdump build-essential libpcap-dev libpcre3-dev zlib1g-dev
 
# Configuration de Snort
sudo mv /etc/snort/snort.conf /etc/snort/snort.conf.bak
cat <<EOF | sudo tee /etc/snort/snort.conf
include /etc/snort/rules/local.rules
output alert_fast: /var/log/snort/alerts
EOF
 
# Création d'une règle pour détecter les injections SQL
sudo mkdir -p /etc/snort/rules
cat <<EOF | sudo tee /etc/snort/rules/local.rules
alert tcp any any -> any 80 (msg:"SQL Injection Detected"; content:"SELECT"; nocase; sid:1000001;)
alert tcp any any -> any 80 (msg:"SQL Injection Detected"; content:"UNION"; nocase; sid:1000002;)
EOF
 
# Redémarrage de Snort
sudo systemctl restart snort
 
echo "Installation et configuration de Snort terminées."

# Installer Apache
echo "Installation d'Apache..."
sudo apt install -y apache2

# Activer les modules nécessaires pour Apache
echo "Activation des modules proxy pour Apache..."
sudo a2enmod proxy proxy_http

# Installer Flask et dépendances Python
echo "Installation de Flask et des dépendances Python..."
sudo apt install -y python3-pip
sudo pip3 install --user flask --break-system-packages
export PYTHONPATH=$PYTHONPATH:/root/.local/lib/python3.12/site-packages
# Créer le répertoire pour l'application Flask dans /var/www/html
APP_DIR="/var/www/html/flask_snort"
sudo mkdir -p $APP_DIR
cd $APP_DIR

# Créer l'application Flask
echo "Création de l'application Flask..."
cat <<EOF > $APP_DIR/app.py
from flask import Flask, render_template, redirect, url_for
import subprocess
import os

app = Flask(__name__)

# Chemin du fichier d'alertes de Snort
ALERT_FILE = "/var/log/snort/alerts"

# Démarrer Snort
def start_snort():
    subprocess.run(["sudo", "snort", "-i", "ens5", "-c", "/etc/snort/snort.conf", "-A", "fast"])

# Arrêter Snort
def stop_snort():
    subprocess.run(["sudo", "systemctl", "stop", "snort"])

# Redémarrer Snort
def restart_snort():
    subprocess.run(["sudo", "systemctl", "restart", "snort"])

# Lire les alertes de Snort
def read_alerts():
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, "r") as f:
            return f.readlines()
    else:
        return ["Aucune alerte disponible."]

@app.route("/")
def index():
    alerts = read_alerts()
    return render_template("alert.html", alerts=alerts)

@app.route("/start")
def start():
    start_snort()
    return redirect(url_for("index"))

@app.route("/stop")
def stop():
    stop_snort()
    return redirect(url_for("index"))

@app.route("/restart")
def restart():
    restart_snort()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOF

# Créer le fichier HTML pour l'interface (alert.html)
echo "Création de la page HTML pour l'interface Flask..."
mkdir -p $APP_DIR/templates
cat <<EOF > $APP_DIR/templates/alert.html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interface Snort - Alertes</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 20px;
            background-color: #f8f9fa;
            color: #333;
        }
        h1 {
            color: #007bff;
        }
        a {
            color: #007bff;
            text-decoration: none;
            margin: 0 10px;
        }
        a:hover {
            text-decoration: underline;
        }
        .alerts {
            background-color: #fff;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        button {
            padding: 10px 15px;
            font-size: 14px;
            background-color: #007bff;
            color: #fff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <h1>Interface de Monitoring Snort</h1>
    <div>
        <a href="/start">Démarrer Snort</a> |
        <a href="/stop">Arrêter Snort</a> |
        <a href="/restart">Redémarrer Snort</a> |
        <a href="index.php?search=">Recherche</a> <!-- Lien vers index.php -->
        <button onclick="window.location.reload();">Recharger</button> <!-- Bouton Reload -->
    </div>
    <h2>Alertes SQL Injection</h2>
    <div class="alerts">
        {% if alerts %}
            <ul>
                {% for alert in alerts %}
                    <li>{{ alert }}</li>
                {% endfor %}
            </ul>
        {% else %}
            <p>Aucune alerte détectée.</p>
        {% endif %}
    </div>
</body>
</html>
EOF

# Donner les droits appropriés à l'utilisateur Apache (www-data)
echo "Configuration des droits pour Apache..."
sudo chown -R www-data:www-data $APP_DIR

# Démarrer Flask sur le port 5000
echo "Démarrage de l'application Flask..."
cd $APP_DIR
nohup python3 app.py &

# Configurer Apache pour rediriger uniquement le chemin /flask vers Flask
echo "Configuration d'Apache pour proxy vers Flask uniquement pour /flask..."
cat <<EOF | sudo tee /etc/apache2/sites-available/000-default.conf
<VirtualHost *:80>
    ServerName localhost

    ProxyPreserveHost On
    
    # Redirection uniquement pour le sous-dossier Flask
    ProxyPass /flask http://127.0.0.1:5000/
    ProxyPassReverse /flask http://127.0.0.1:5000/

    # Permettre à Apache de gérer les autres fichiers, y compris index.php
    DocumentRoot /var/www/html
    DirectoryIndex index.php index.html
    <Directory /var/www/html>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
EOF

# Redémarrer Apache pour appliquer la configuration
echo "Redémarrage d'Apache..."
sudo systemctl restart apache2
