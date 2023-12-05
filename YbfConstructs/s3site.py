from typing import Optional
from typing import Sequence

from aws_cdk import Duration
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_route53 as rt53
from aws_cdk import aws_route53_targets as rt53_targets
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from constructs import Construct


class SiteDeploy(Construct):
    """Represents a construct to deploy a static site to S3

    This construct will additionally add a domain name to the site
    and will redirect all HTTP to HTTPS
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        sources: Sequence[s3deploy.ISource],
        certificate: acm.ICertificate,
        domain_name: str,
        route53_zone: rt53.IHostedZone,
        bucket_name: Optional[str] = None,
        prune_bucket: Optional[bool] = False,
        root_object: Optional[str] = "index.html",
        website_error_document: Optional[str] = "404.html",
    ) -> None:
        super().__init__(scope, id)

        if bucket_name is None:
            self.pkgBucket = s3.Bucket(
                self,
                "SiteBucket",
                public_read_access=True,
                block_public_access=s3.BlockPublicAccess(
                    block_public_acls=False,
                    ignore_public_acls=False,
                    block_public_policy=False,
                    restrict_public_buckets=False,
                ),
                website_error_document=website_error_document,
                website_index_document=root_object,
            )
        else:
            self.pkgBucket = s3.Bucket.from_bucket_name(
                self, "SiteBucket", bucket_name)

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.pkgBucket),
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,  # noqa: E501
            ),
            default_root_object=root_object,
            domain_names=[domain_name],
            certificate=certificate,
        )

        rt53.ARecord(
            self,
            "DnsRecord",
            record_name=domain_name,
            zone=route53_zone,
            target=rt53.RecordTarget.from_alias(
                rt53_targets.CloudFrontTarget(self.distribution)
            ),
        )

        s3deploy.BucketDeployment(
            self,
            "WebsiteFiles",
            sources=sources,
            destination_bucket=self.pkgBucket,
            distribution=self.distribution,
            prune=prune_bucket,
            cache_control=[
                s3deploy.CacheControl.max_age(Duration.days(365)),
                s3deploy.CacheControl.immutable(),
            ],
        )


class StaticHTMLSiteDeploy(SiteDeploy):
    def __init__(
            self, scope: Construct, id: str, local_dir: str, **kwargs) -> None:
        sources = [s3deploy.Source.asset(local_dir)]
        super().__init__(scope, id, sources=sources, **kwargs)

        html_assets = [
            s3deploy.Source.asset(
                local_dir, exclude=["*", "!*.html", "!**/*.html"])
        ]
        s3deploy.BucketDeployment(
            self,
            "HTMLFiles",
            sources=html_assets,
            destination_bucket=self.pkgBucket,
            distribution=self.distribution,
            prune=False,
            cache_control=[
                s3deploy.CacheControl.max_age(Duration.days(0)),
            ],
            content_type="text/html",
        )
