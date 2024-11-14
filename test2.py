import boto3
from botocore.exceptions import ClientError

# Initialisation du client EC2
ec2 = boto3.client('ec2')
key_name = "my-key-pair"
vpc_name = "MyVPC"
public_subnet_name = "PublicSubnet"
private_subnet_name = "PrivateSubnet"

# Identifiants existants pour les ressources créées manuellement
vpc_id = "vpc-07efe9fb080ab3642"  # ID du VPC créé
public_subnet_id = "subnet-06edeaee88116d406"  # ID du sous-réseau public créé
private_subnet_id = "subnet-08caaa226be6a240f"  # ID du sous-réseau privé créé
web_sg_id = "sg-0db71e0e613ff41d6"  # ID du groupe de sécurité pour le serveur Web
db_sg_id = "sg-0847b44ca1add12b7"   # Groupe de sécurité pour le serveur BDD

ami_id = "ami-007868005aea67c54"  # Remplacez par un ID d'AMI valide

try:
    # Création de l'instance EC2 pour le serveur Web
    web_instance_response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType='t2.micro',
        KeyName=key_name,
        UserData='file://web_server_setup.sh',
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
        UserData='file://db_server_setup.sh',
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

    print("Instances EC2 créées avec succès.")
except ClientError as e:
    print(f"Une erreur est survenue : {e}")