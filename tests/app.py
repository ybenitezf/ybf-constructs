#!/usr/bin/env python3
from aws_cdk import aws_route53 as rt53
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_s3_deployment as s3deploy
from aws_cdk import App, Environment, Stack
from constructs import Construct
from YbfConstructs.s3site import SiteDeploy
from dotenv import load_dotenv
import os


load_dotenv()


env = Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')
)


class ProbeStack(Stack):

    def __init__(
            self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cert = acm.Certificate.from_certificate_arn(
            self, "Certificate",
            os.getenv('TESTSITE_CERTIFICATE')
        )

        zone = rt53.HostedZone.from_lookup(
            self, 'DnsZone',
            domain_name=os.getenv("ZONE_DOMAIN_NAME")
        )

        site = SiteDeploy(
            self, 'MyTestSite',
            sources=[s3deploy.Source.asset("./holder")],
            certificate=cert,
            domain_name=os.getenv('TEST_HOST_NAME'),
            route53_zone=zone,
            prune_bucket=True)


app = App()
ProbeStack(app, "MyTestStack", env=env)

app.synth()
