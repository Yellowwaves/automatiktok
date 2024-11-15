import boto3
from botocore.exceptions import ClientError

userdata_web = '''#!/bin/bash
# Mise à jour et installation d'Apache et PHP
apt update
apt install -y apache2 php php-mysql

# Configurer Apache pour écouter sur toutes les interfaces
sed -i 's/Listen 80/Listen 0.0.0.0:80/' /etc/apache2/ports.conf

# Démarrer Apache
systemctl start apache2
systemctl enable apache2

# Créer une page PHP vulnérable aux injections SQL
cat <<EOL > /var/www/html/index.php
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recherche d'utilisateurs</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            color: #333;
            text-align: center;
            padding: 20px;
        }
        h1 {
            color: #007bff;
        }
        .search-container {
            margin: 20px auto;
            max-width: 600px;
        }
        input[type="text"] {
            padding: 10px;
            font-size: 16px;
            width: 70%;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-right: 10px;
        }
        input[type="submit"] {
            padding: 10px 20px;
            font-size: 16px;
            color: #fff;
            background-color: #007bff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #0056b3;
        }
        .results {
            margin-top: 20px;
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        .result-item {
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
    </style>
</head>
<body>
    <h1>Recherche d'utilisateurs</h1>
    <div class="search-container">
        <form action="index.php" method="get">
            <input type="text" name="search" placeholder="Recherchez un nom" required>
            <input type="submit" value="Rechercher">
        </form>
    </div>
    <div class="results">
        <?php
        \$servername = "localhost";
        \$username = "testuser";
        \$password = "password";
        \$dbname = "testdb";

        // Créer une connexion à la base de données
        \$conn = new mysqli(\$servername, \$username, \$password, \$dbname);

        // Vérifier la connexion
        if (\$conn->connect_error) {
            die("Connexion échouée: " . \$conn->connect_error);
        }

        // Vérification de la présence d'un paramètre de recherche
        if (isset(\$_GET['search'])) {
            \$search = \$_GET['search'];
            // Requête SQL vulnérable
            \$sql = "SELECT * FROM utilisateurs WHERE nom LIKE '%\$search%'";
            \$result = \$conn->query(\$sql);

            if (\$result->num_rows > 0) {
                while(\$row = \$result->fetch_assoc()) {
                    echo "<div class='result-item'><strong>Nom:</strong> " . htmlspecialchars(\$row["nom"]) . " - <strong>Email:</strong> " . htmlspecialchars(\$row["email"]) . "</div>";
                }
            } else {
                echo "<p>Aucun résultat trouvé.</p>";
            }
        } else {
            echo "<p>Entrez un terme de recherche dans la barre ci-dessus.</p>";
        }

        \$conn->close();
        ?>
    </div>
</body>
</html>
EOL


# Vérifier si Apache fonctionne
systemctl restart apache2
systemctl status apache2

# Vérifier si le port 80 est bien ouvert
netstat -tuln | grep ':80'
'''

userdata_bdd = '''#!/bin/bash
# Mise à jour et installation de MariaDB
apt update
apt install -y mariadb-server

# Configurer MariaDB pour écouter sur toutes les interfaces
sed -i 's/^bind-address.*=.*127.0.0.1/bind-address = 0.0.0.0/' /etc/mysql/mariadb.conf.d/50-server.cnf

# Démarrer MariaDB et activer le démarrage automatique
systemctl start mariadb
systemctl enable mariadb

# Vérifier que MariaDB écoute sur toutes les interfaces
systemctl restart mariadb
netstat -tuln | grep ':3306'

# Création de la base de données, de l'utilisateur et de la table vulnérable
mysql -u root <<EOF
CREATE DATABASE testdb;
CREATE USER 'testuser'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON testdb.* TO 'testuser'@'%';
FLUSH PRIVILEGES;

USE testdb;
CREATE TABLE utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL
);

INSERT INTO utilisateurs (nom, email) VALUES ('Alice', 'alice@example.com');
INSERT INTO utilisateurs (nom, email) VALUES ('Bob', 'bob@example.com');
INSERT INTO utilisateurs (nom, email) VALUES ('Charlie', 'charlie@example.com');
EOF
'''

def get_private_ip(ec2, instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response['Reservations'][0]['Instances'][0]['PrivateIpAddress']


def create_key_pair(ec2, key_name):
    try:
        ec2.describe_key_pairs(KeyNames=[key_name])
        print(f"La clé {key_name} existe déjà.")
    except ClientError:
        key_pair = ec2.create_key_pair(KeyName=key_name)
        with open(f"{key_name}.pem", "w") as file:
            file.write(key_pair['KeyMaterial'])
        print(f"Clé {key_name} créée et enregistrée localement.")

# Initialisation du client EC2
ec2 = boto3.client('ec2')
key_name = "my-key-pair"

# Création de la clé si elle n'existe pas
create_key_pair(ec2, key_name)

try:
    # 1. Création du VPC
    vpc_response = ec2.create_vpc(CidrBlock='172.16.0.0/16')
    vpc_id = vpc_response['Vpc']['VpcId']
    ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': 'MyVPC'}])
    print(f"VPC créé avec ID : {vpc_id}")

    # 2. Création des sous-réseaux
    # Sous-réseau public
    public_subnet_response = ec2.create_subnet(
        VpcId=vpc_id,
        CidrBlock='172.16.1.0/24',
        AvailabilityZone='us-east-1a'
    )
    public_subnet_id = public_subnet_response['Subnet']['SubnetId']
    ec2.create_tags(Resources=[public_subnet_id], Tags=[{'Key': 'Name', 'Value': 'PublicSubnet'}])
    print(f"Sous-réseau public créé avec ID : {public_subnet_id}")

    # Sous-réseau privé
    private_subnet_response = ec2.create_subnet(
        VpcId=vpc_id,
        CidrBlock='172.16.2.0/24',
        AvailabilityZone='us-east-1a'
    )
    private_subnet_id = private_subnet_response['Subnet']['SubnetId']
    ec2.create_tags(Resources=[private_subnet_id], Tags=[{'Key': 'Name', 'Value': 'PrivateSubnet'}])
    print(f"Sous-réseau privé créé avec ID : {private_subnet_id}")

    # 3. Internet Gateway et attachement au VPC
    igw_response = ec2.create_internet_gateway()
    igw_id = igw_response['InternetGateway']['InternetGatewayId']
    ec2.attach_internet_gateway(VpcId=vpc_id, InternetGatewayId=igw_id)
    print(f"Internet Gateway créé et attaché au VPC : {igw_id}")

    # 4. Table de routage pour le sous-réseau public
    public_route_table_response = ec2.create_route_table(VpcId=vpc_id)
    public_route_table_id = public_route_table_response['RouteTable']['RouteTableId']
    ec2.create_route(RouteTableId=public_route_table_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
    ec2.associate_route_table(RouteTableId=public_route_table_id, SubnetId=public_subnet_id)
    print("Table de routage public créée et associée au sous-réseau public")

    # 5. NAT Gateway pour le sous-réseau privé
    eip_response = ec2.allocate_address(Domain='vpc')
    eip_alloc_id = eip_response['AllocationId']
    nat_gw_response = ec2.create_nat_gateway(SubnetId=public_subnet_id, AllocationId=eip_alloc_id)
    nat_gw_id = nat_gw_response['NatGateway']['NatGatewayId']
    print(f"NAT Gateway créé avec ID : {nat_gw_id}")
    ec2.get_waiter('nat_gateway_available').wait(NatGatewayIds=[nat_gw_id])

    # 6. Table de routage pour le sous-réseau privé
    private_route_table_response = ec2.create_route_table(VpcId=vpc_id)
    private_route_table_id = private_route_table_response['RouteTable']['RouteTableId']
    ec2.create_route(RouteTableId=private_route_table_id, DestinationCidrBlock='0.0.0.0/0', NatGatewayId=nat_gw_id)
    ec2.associate_route_table(RouteTableId=private_route_table_id, SubnetId=private_subnet_id)
    print("Table de routage privé créée et associée au sous-réseau privé")

    # 7. Groupes de sécurité
    # Serveur Web
    web_sg_response = ec2.create_security_group(GroupName='WebServerSG', Description="SG pour Web Server", VpcId=vpc_id)
    web_sg_id = web_sg_response['GroupId']

    # Autoriser les règles de sécurité pour le serveur Web
    ec2.authorize_security_group_ingress(GroupId=web_sg_id, IpProtocol='tcp', FromPort=80, ToPort=80, CidrIp='0.0.0.0/0')
    ec2.authorize_security_group_ingress(GroupId=web_sg_id, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp='0.0.0.0/0')
    print(f"Groupe de sécurité pour serveur Web créé avec ID : {web_sg_id}")

    # Serveur BDD
    db_sg_response = ec2.create_security_group(GroupName='DBServerSG', Description="SG pour DB Server", VpcId=vpc_id)
    db_sg_id = db_sg_response['GroupId']
    ec2.authorize_security_group_ingress(
        GroupId=db_sg_id,
        IpPermissions=[{
            'IpProtocol': 'tcp',
            'FromPort': 3306,
            'ToPort': 3306,
            'UserIdGroupPairs': [{'GroupId': web_sg_id}]
        }]
    )
    print(f"Groupe de sécurité pour serveur BDD créé avec ID : {db_sg_id}")

    # 8. Instances EC2
    ami_id = "ami-0866a3c8686eaeeba"  # Remplacez par un ID d'AMI valide

    # Lancement de l'instance de base de données
    db_instance_response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType='t3.micro',
        KeyName=key_name,
        UserData=userdata_bdd,
        MinCount=1,
        MaxCount=1,
        NetworkInterfaces=[{
            'SubnetId': private_subnet_id,
            'DeviceIndex': 0,
            'Groups': [db_sg_id],
        }]
    )
    db_instance_id = db_instance_response['Instances'][0]['InstanceId']
    print(f"Instance de base de données lancée avec ID : {db_instance_id}")

    # Attendre que l'instance DB soit en cours d'exécution
    ec2.get_waiter('instance_running').wait(InstanceIds=[db_instance_id])
    db_private_ip = get_private_ip(ec2, db_instance_id)
    print(f"Adresse IP privée du serveur BDD : {db_private_ip}")

    # Modifier le script userdata du serveur web avec l'IP du serveur BDD
    userdata_web_updated = userdata_web.replace("localhost", db_private_ip)

    # Lancement de l'instance serveur web
    web_instance_response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType='t3.micro',
        KeyName=key_name,
        UserData=userdata_web_updated,
        MinCount=1,
        MaxCount=1,
        NetworkInterfaces=[{
            'AssociatePublicIpAddress': True,
            'SubnetId': public_subnet_id,
            'DeviceIndex': 0,
            'Groups': [web_sg_id],
        }]
    )
    web_instance_id = web_instance_response['Instances'][0]['InstanceId']
    print(f"Instance de serveur Web lancée avec ID : {web_instance_id}")

    print("Infrastructure déployée avec succès.")
except ClientError as e:
    print(f"Une erreur est survenue : {e}")
