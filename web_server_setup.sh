#!/bin/bash

# Mettre à jour le système
apt update -y 

# Installer Apache
apt install -y apache2 

# Configurer Apache pour écouter sur toutes les interfaces
sed -i 's/Listen 80/Listen 0.0.0.0:80/' /etc/apache2/ports.conf

# Démarrer Apache
systemctl start apache2
systemctl enable apache2

# Créer une page d'accueil avec un design plus joli
echo "<!DOCTYPE html>
<html lang='fr'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Bienvenue sur le serveur Apache</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            text-align: center;
            background-color: #ffffff;
            padding: 50px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            max-width: 600px;
            width: 100%;
        }
        h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 20px;
        }
        p {
            color: #777;
            font-size: 1.2em;
        }
        .button {
            background-color: #4CAF50;
            color: white;
            padding: 15px 20px;
            font-size: 1.2em;
            text-decoration: none;
            border-radius: 5px;
            display: inline-block;
            margin-top: 20px;
        }
        .button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class='container'>
        <h1>Bienvenue sur votre serveur Apache!</h1>
        <p>Le serveur fonctionne correctement.</p>
        <a href='#' class='button'>Découvrir plus</a>
    </div>
</body>
</html>" > /var/www/html/index.html

# Vérifier si Apache fonctionne
systemctl restart apache2
systemctl status apache2

# Vérifier si le port 80 est bien ouvert
netstat -tuln | grep ':80'

# Assurez-vous que le fichier index.html a les bonnes permissions
chmod 644 /var/www/html/index.html