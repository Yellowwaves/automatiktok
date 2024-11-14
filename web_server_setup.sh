#!/bin/bash
# Mettre à jour les paquets et installer Apache
yum update -y
yum install -y httpd

# Démarrer le service Apache et activer le démarrage automatique
systemctl start httpd
systemctl enable httpd

# Créer une page d'accueil simple
echo "<html><body><h1>Bienvenue sur le serveur web Apache!</h1></body></html>" > /var/www/html/index.html

# Autoriser le trafic HTTP dans le pare-feu (si nécessaire)
firewall-cmd --permanent --add-service=http
firewall-cmd --reload