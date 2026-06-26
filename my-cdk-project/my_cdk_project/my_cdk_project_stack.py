from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    Tags,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_sns as sns,
)
from constructs import Construct


class CarbonMappingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Tags.of(self).add("Project", "CarbonMapping")
        Tags.of(self).add("Environment", "production")

        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=1, 
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="App",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Db",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        app_sg = ec2.SecurityGroup(
            self,
            "AppSecurityGroup",
            vpc=vpc,
            description="Dagster / orchestration hosts",
            allow_all_outbound=True,
        )

        db_sg = ec2.SecurityGroup(
            self,
            "DbSecurityGroup",
            vpc=vpc,
            description="CarbonMapping RDS Postgres",
            allow_all_outbound=False,
        )
        db_sg.add_ingress_rule(
            app_sg,
            ec2.Port.tcp(5432),
            "Postgres from application tier only",
        )

        database = rds.DatabaseInstance(
            self,
            "Postgres",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.of("16.14", "16"),
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T4G,
                ec2.InstanceSize.MICRO,  # db.t4g.micro
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            security_groups=[db_sg],
            publicly_accessible=False,
            multi_az=False,
            credentials=rds.Credentials.from_generated_secret(
                "postgres",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/@\"\\",
            ),
            database_name="CarbonMapping",
            allocated_storage=20,
            max_allocated_storage=100,  # autoscale storage
            storage_type=rds.StorageType.GP3,
            storage_encrypted=True,
            backup_retention=Duration.days(14),
            preferred_backup_window="03:00-04:00",
            preferred_maintenance_window="sun:04:00-sun:05:00",
            deletion_protection=True,
            removal_policy=RemovalPolicy.SNAPSHOT,  # or RETAIN
            auto_minor_version_upgrade=True,
            cloudwatch_logs_exports=["postgresql"],
            enable_performance_insights=True,
            performance_insight_retention=rds.PerformanceInsightRetention.DEFAULT,
            monitoring_interval=Duration.seconds(60),
        )

        alarm_topic = sns.Topic(self, "DbAlarmTopic")
        cpu_alarm = cloudwatch.Alarm(
            self,
            "DbCpuAlarm",
            metric=database.metric_cpu_utilization(),
            threshold=80,
            evaluation_periods=3,
            datapoints_to_alarm=2,
        )
        cpu_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        CfnOutput(self, "DbEndpoint", value=database.db_instance_endpoint_address)
        CfnOutput(self, "DbSecretArn", value=database.secret.secret_arn)
        CfnOutput(self, "AppSecurityGroupId", value=app_sg.security_group_id)