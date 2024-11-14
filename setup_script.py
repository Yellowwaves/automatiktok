import boto3
from botocore.exceptions import ClientError

userdata_web = '''#!/bin/bash
# Mise à jour et installation d'Apache
apt update

# Installer Apache
apt install -y apache2 

# Configurer Apache pour écouter sur toutes les interfaces
sed -i 's/Listen 80/Listen 0.0.0.0:80/' /etc/apache2/ports.conf

# Démarrer Apache
systemctl start apache2
systemctl enable apache2


# Créer une page d'accueil simple
echo "<html><body><h1>Bienvenue sur votre serveur Apache!</h1></body></html>" > /var/www/html/index.html

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

# Démarrer MariaDB et activer le démarrage automatique
systemctl start mariadb
systemctl enable mariadb

# Création de la base de données et de l'utilisateur
mysql -u root <<EOF
CREATE DATABASE testdb;
CREATE USER 'testuser'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON testdb.* TO 'testuser'@'%';
FLUSH PRIVILEGES;
EOF
'''
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
    # Définit l'ID du VPC pour les groupes de sécurité
    print (f"vpc id {vpc_id}")
    # Serveur Web
    # Utilisation de vpc_id pour créer le groupe de sécurité dans le bon VPC
    web_sg_response = ec2.create_security_group(GroupName='WebServerSG', Description="SG pour Web Server", VpcId=vpc_id)
    web_sg_id = web_sg_response['GroupId']

    # Autoriser les règles de sécurité pour le serveur Web
    ec2.authorize_security_group_ingress(GroupId=web_sg_id, IpProtocol='tcp', FromPort=80, ToPort=80, CidrIp='0.0.0.0/0')
    ec2.authorize_security_group_ingress(GroupId=web_sg_id, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp='0.0.0.0/0')

    print(f"Groupe de sécurité pour serveur Web créé avec ID : {web_sg_id}")

    # Serveur BDD
    db_sg_response = ec2.create_security_group(GroupName='DBServerSG', Description="SG pour DB Server", VpcId=vpc_id)
    db_sg_id = db_sg_response['GroupId']
    # Autoriser l'accès du groupe WebServerSG au groupe DBServerSG via le port 3306
    ec2.authorize_security_group_ingress(
        GroupId=db_sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 3306,
                'ToPort': 3306,
                'UserIdGroupPairs': [
                    {
                        'GroupId': web_sg_id
                    }
                ]
            }
        ]
    )
    print(f"Groupe de sécurité pour serveur BDD créé avec ID : {db_sg_id}")

    # 8. Instances EC2
    ami_id = "ami-0866a3c8686eaeeba"  # Remplacez par un ID d'AMI valide

    # Web server
    # Création de l'instance EC2 pour le serveur Web
    web_instance_response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType='t2.micro',
        KeyName=key_name,
        UserData=userdata_web,
        MinCount=1,
        MaxCount=1,
        NetworkInterfaces=[{
            'AssociatePublicIpAddress': True,  # Association de l'adresse IP publique
            'SubnetId': public_subnet_id,      # Sous-réseau à utiliser
            'DeviceIndex': 0,
            'Groups': [web_sg_id],  # Spécifier le groupe de sécurité ici
        }]
    )
    web_instance_id = web_instance_response['Instances'][0]['InstanceId']
    print(f"Instance de serveur Web lancée avec ID : {web_instance_id}")

    # Création de l'instance EC2 pour le serveur BDD
    db_instance_response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType='t2.micro',
        KeyName=key_name,
        UserData=userdata_bdd,
        MinCount=1,
        MaxCount=1,
        NetworkInterfaces=[{
            'SubnetId': private_subnet_id,  # Sous-réseau privé pour la base de données
            'DeviceIndex': 0,
            'Groups': [db_sg_id],  # Spécifier le groupe de sécurité ici
        }]
    )
    db_instance_id = db_instance_response['Instances'][0]['InstanceId']
    print(f"Instance de base de données lancée avec ID : {db_instance_id}")

    print("VPC et infrastructure déployés avec succès.")
except ClientError as e:
    print(f"Une erreur est survenue : {e}")
