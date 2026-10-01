from aws_cdk import Duration, Stack, aws_s3 as s3, aws_lambda as _lambda
from constructs import Construct
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_bedrockagentcore as agentcore
from aws_cdk import aws_iam as iam
from typing import cast
from aws_cdk import aws_logs as logs
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_ec2 as ec2 
from aws_cdk import aws_rds as rds
import aws_cdk as cdk
from aws_cdk import aws_iam as iam


class GNyRStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,  kb_id: str = "", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        bucket = s3.Bucket(self, "BucketRecetasGNyR")
        funcion = _lambda.Function(
            self,
            "FuncionPruebaGNyR",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=_lambda.Code.from_inline("def handler(event, context):\n    return {'status': 'ok'}"),
        )
        bucket.grant_read(funcion)

        tabla_nevera = dynamodb.Table( 
            self, "TablaNevera", 
            partition_key=dynamodb.Attribute(name="ingrediente", type=dynamodb.AttributeType.STRING), 
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST, ) 
        
        funcion_nevera = _lambda.Function( 
            self, "FuncionGestionarNevera", 
            runtime=_lambda.Runtime.PYTHON_3_13, 
            handler="handler.lambda_handler", 
            code=_lambda.Code.from_asset("lambda_gestionar_nevera"), 
            timeout=Duration.seconds(30),
            environment={"TABLE_NAME": tabla_nevera.table_name}, ) 
        
        funcion_recetas = _lambda.Function( 
            self, "FuncionConsultarRecetas", 
            runtime=_lambda.Runtime.PYTHON_3_13, 
            handler="handler.lambda_handler", 
            code=_lambda.Code.from_asset("lambda_consultar_recetas"), 
            timeout=Duration.seconds(60),
            environment={"KB_ID": kb_id}, )

        funcion_recetas.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:Retrieve"],
                resources=[
                    f"arn:aws:bedrock:eu-south-2:{self.account}:knowledge-base/{kb_id}"
                ] if kb_id else ["*"],
            )
        )
        
        gateway = agentcore.Gateway( 
            self, "GatewayGNyR", 
            gateway_name="gateway-gnyr", 
            authorizer_configuration=agentcore.GatewayAuthorizer.using_aws_iam(), )
        
        gateway.add_lambda_target( 
            "NeveraTarget", 
            gateway_target_name="nevera-target", 
            lambda_function=cast(_lambda.IFunction, funcion_nevera), 
            tool_schema=agentcore.ToolSchema.from_inline([
                {
                    "name": "gestionar_nevera",
                    "description": "Anade ingredientes a la nevera o consulta lo que hay.",
                    "inputSchema": {
                        "type": agentcore.SchemaDefinitionType.OBJECT,
                        "properties": {
                            "accion": {"type": agentcore.SchemaDefinitionType.STRING},
                            "ingrediente": {"type": agentcore.SchemaDefinitionType.STRING},
                            "cantidad": {"type": agentcore.SchemaDefinitionType.STRING},
                        },
                        "required": ["accion"],
                    },
                }
            ]),
        )

        gateway.add_lambda_target(
            "RecetasTarget",
            gateway_target_name="recetas-target",
            lambda_function=cast(_lambda.IFunction, funcion_recetas),
            tool_schema=agentcore.ToolSchema.from_inline([
                {
                    "name": "consultar_recetas",
                    "description": "Busca informacion sobre recetas de cocina que tenga en la base de datos.",
                    "inputSchema": {
                        "type": agentcore.SchemaDefinitionType.OBJECT,
                        "properties": {
                            "pregunta": {"type": agentcore.SchemaDefinitionType.STRING}
                        },
                        "required": ["pregunta"],
                    },
                }
            ]),
        )
        
        log_group = logs.LogGroup( self, "AgenteLogGroup", log_group_name="/aws/vendedlogs/bedrock-agentcore/agente-gnyr", ) 
        
        runtime = agentcore.Runtime(
            self,
            "RuntimeGNyRV2",
            runtime_name="agente_gnyrV2",
            agent_runtime_artifact=agentcore.AgentRuntimeArtifact.from_asset(                
                directory="agente_gnyr",
                platform=ecr_assets.Platform.LINUX_ARM64, 
            ),
            environment_variables={"GATEWAY_URL": gateway.gateway_url or ""},
            tracing_enabled=True, 
            logging_configs=[
                agentcore.LoggingConfig( 
                    log_type=agentcore.LogType.APPLICATION_LOGS, 
                    destination=agentcore.LoggingDestination.cloud_watch_logs(log_group), )],
        )

        runtime.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock-agentcore:InvokeGateway"],
            resources=["*"],
        ))
        
        runtime.add_to_role_policy(iam.PolicyStatement( 
            actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"], 
            resources=[ f"arn:aws:bedrock:eu-south-2:{self.account}:inference-profile/eu.anthropic.claude-haiku-4-5-20251001-v1:0", "arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-*", ], 
        ))
    
        tabla_nevera.grant_read_write_data(funcion_nevera)
        bucket_recetas = s3.Bucket(self, "BucketDocsRecetas")
        
        oidc_provider = iam.OpenIdConnectProvider( 
            self, 
            "GithubOidc", 
            url="https://token.actions.githubusercontent.com", 
            client_ids=["sts.amazonaws.com"], ) 
        
        deploy_role = iam.Role( 
            self, "GithubActionsDeployRole", 
            assumed_by=iam.FederatedPrincipal( 
                oidc_provider.open_id_connect_provider_arn, 
                conditions={ "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"}, 
                            "StringLike": {"token.actions.githubusercontent.com:sub": "repo:kewayik/gnyr:*"}, }, 
                assume_role_action="sts:AssumeRoleWithWebIdentity", ), 
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")], 
        )
        
        '''
        vpc = ec2.Vpc.from_lookup(self, "VpcPorDefecto", is_default=True)
                
        sg_ec2 = ec2.SecurityGroup(
            self, "SgEc2Prueba",
            vpc=vpc,
            description="SSH desde mi IP",
            allow_all_outbound=True,
        )
            
        sg_ec2.add_ingress_rule(
            ec2.Peer.ipv6("2a0c:5a86:3901:5f01::1d9b/128"),
            ec2.Port.tcp(22),
            "SSH desde mi IP (IPv6)",
        )

        instancia = ec2.Instance(
            self, "Ec2Prueba",
            vpc=vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            security_group=sg_ec2,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )
        
        sg_rds = ec2.SecurityGroup( 
            self, 
            "SgRdsPrueba", 
            vpc=vpc, 
            description="Postgres solo desde el EC2 de prueba", 
            allow_all_outbound=True, 
        ) 
        
        sg_rds.add_ingress_rule( 
            ec2.Peer.security_group_id(sg_ec2.security_group_id), 
            ec2.Port.tcp(5432), 
            "Postgres desde el EC2 de prueba", 
        )
        
        db = rds.DatabaseInstance(
            self, "RdsPrueba",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[sg_rds],
            credentials=rds.Credentials.from_generated_secret("postgres_admin"),
            allocated_storage=20,
            delete_automated_backups=True,
            deletion_protection=False,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        '''