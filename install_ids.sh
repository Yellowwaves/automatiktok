#!/bin/bash
# Script d'installation de Snort avec toutes les dépendances nécessaires sur une instance Amazon Linux 2

# Mettre à jour le système
sudo yum update -y

# Installer les outils de développement nécessaires
sudo yum groupinstall -y "Development Tools"
sudo yum install -y gcc-c++ flex bison zlib zlib-devel libpcap libpcap-devel pcre pcre-devel libdnet libdnet-devel tcpdump

# Si libpcap n'est pas correctement installé, installer manuellement
cd /tmp
if ! ldconfig -p | grep -q libpcap; then
    wget http://www.tcpdump.org/release/libpcap-1.9.1.tar.gz
    tar -xzf libpcap-1.9.1.tar.gz
    cd libpcap-1.9.1
    ./configure
    make
    sudo make install
    cd ..
fi

# Télécharger et installer Snort
wget https://www.snort.org/downloads/snort/snort-2.9.20.tar.gz
tar -xvzf snort-2.9.20.tar.gz
cd snort-2.9.20
./configure --enable-sourcefire --with-libpcap-libraries=/usr/local/lib --with-libpcap-includes=/usr/local/include --with-pcre-libraries=/usr/lib --with-pcre-includes=/usr/include
make
sudo make install

# Configurer les dossiers et les règles de Snort
sudo mkdir -p /etc/snort/rules
sudo mkdir -p /var/log/snort
sudo mkdir -p /usr/local/lib/snort_dynamicrules
sudo touch /etc/snort/rules/local.rules
sudo touch /etc/snort/snort.conf

# Ajouter une règle de détection d'injection SQL dans les règles locales
echo 'alert tcp any any -> any 80 (msg:"SQL Injection attempt detected"; content:"union"; nocase; sid:1000001; rev:1;)' | sudo tee -a /etc/snort/rules/local.rules

# Configurer Snort pour inclure les règles locales
echo 'include $RULE_PATH/local.rules' | sudo tee -a /etc/snort/snort.conf

# Changer les permissions du dossier de logs
sudo chown -R $(whoami) /var/log/snort

# Vérifier que Snort est installé
snort -V