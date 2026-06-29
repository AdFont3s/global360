from diagrams import Diagram, Cluster, Edge
from diagrams.aws.network import VPC, InternetGateway, NATGateway, ElasticLoadBalancing, Route53
from diagrams.aws.compute import EC2AutoScaling, EC2
from diagrams.onprem.client import Users

graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "pad": "0.5",
    "splines": "ortho",
}

with Diagram(
    "Global360 Auto-Healing Web Tier",
    filename="docs/architecture",
    outformat="png",
    graph_attr=graph_attr,
    show=False,
):
    users = Users("Internet")

    with Cluster("AWS ap-southeast-2\nVPC 10.0.0.0/16"):

        igw = InternetGateway("Internet Gateway")

        with Cluster("Public Subnets\n10.0.1.0/24 | 10.0.2.0/24"):
            alb = ElasticLoadBalancing("Application\nLoad Balancer")
            nat = NATGateway("NAT Gateway\n(AZ-a)")

        with Cluster("Private Subnets\n10.0.11.0/24 | 10.0.12.0/24"):
            ec2a = EC2("EC2 (AZ-a)\nt3.micro\nNGINX/Docker")
            ec2b = EC2("EC2 (AZ-b)\nt3.micro\nNGINX/Docker")

    users >> Edge(label="HTTP :80") >> igw >> alb
    alb >> Edge(label="HTTP :80") >> ec2a
    alb >> Edge(label="HTTP :80") >> ec2b
    ec2a >> Edge(label="outbound", style="dashed") >> nat
    ec2b >> Edge(label="outbound", style="dashed") >> nat
    nat >> Edge(style="dashed") >> igw
