#!/bin/bash
# Mettre à jour les paquets et installer MariaDB
yum update -y
yum install -y mariadb-server

# Démarrer le service MariaDB et activer le démarrage automatique
systemctl start mariadb
systemctl enable mariadb

# Créer une base de données et un utilisateur de base
mysql -u root <<EOF
CREATE DATABASE testdb;
CREATE USER 'testuser'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON testdb.* TO 'testuser'@'%';
FLUSH PRIVILEGES;
EOF