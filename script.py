import boto3
from botocore.exceptions import ClientError

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
    ec2.authorize_security_group_ingress(GroupId=web_sg_id, IpProtocol='tcp', FromPort=80, ToPort=80, CidrIp='0.0.0.0/0')
    ec2.authorize_security_group_ingress(GroupId=web_sg_id, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp='0.0.0.0/0')
    print(f"Groupe de sécurité pour serveur Web créé avec ID : {web_sg_id}")

    # Serveur BDD
    db_sg_response = ec2.create_security_group(GroupName='DBServerSG', Description="SG pour DB Server", VpcId=vpc_id)
    db_sg_id = db_sg_response['GroupId']
    ec2.authorize_security_group_ingress(GroupId=db_sg_id, IpProtocol='tcp', FromPort=3306, ToPort=3306, SourceSecurityGroupName='WebServerSG')
    print(f"Groupe de sécurité pour serveur BDD créé avec ID : {db_sg_id}")

    # 8. Instances EC2
    ami_id = input("Entrez l'ID de l'AMI choisie : ")

    # Web server
    web_instance_response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType='t2.micro',
        KeyName=key_name,
        SubnetId=public_subnet_id,
        AssociatePublicIpAddress=True,
        SecurityGroupIds=[web_sg_id],
        UserData='file://web_server_setup.sh',
        MinCount=1,
        MaxCount=1
    )
    web_instance_id = web_instance_response['Instances'][0]['InstanceId']
    print(f"Instance de serveur Web lancée avec ID : {web_instance_id}")

    # Serveur BDD
    db_instance_response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType='t2.micro',
        KeyName=key_name,
        SubnetId=private_subnet_id,
        SecurityGroupIds=[db_sg_id],
        UserData='file://db_server_setup.sh',
        MinCount=1,
        MaxCount=1
    )
    db_instance_id = db_instance_response['Instances'][0]['InstanceId']
    print(f"Instance de base de données lancée avec ID : {db_instance_id}")

    print("VPC et infrastructure déployés avec succès.")
except ClientError as e:
    print(f"Une erreur est survenue : {e}")
