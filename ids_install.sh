#!/bin/bash
 
# Mise à jour du système
sudo apt update && sudo apt upgrade -y
 
# Installation des dépendances
sudo apt install -y snort tcpdump build-essential libpcap-dev libpcre3-dev zlib1g-dev
 
# Installation de Snort
sudo apt install -y snort
 
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

