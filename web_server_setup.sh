#cloud-boothook
#!/bin/bash

yum update -y 
yum install -y httpd.x86_64 
systemctl start httpd
systemctl enable httpd


# Créer une page d'accueil simple
echo "<html><body><h1>Bienvenue sur le serveur web Apache!</h1></body></html>" > /var/www/html/index.html

# Autoriser le trafic HTTP dans le pare-feu (si nécessaire)
firewall-cmd --permanent --add-service=http
firewall-cmd --reload