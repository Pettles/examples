from aws_cdk import (
    Stack, Stage,
    aws_ssm as ssm,
    pipelines,
)
from constructs import Construct

from settings import settings


class DeploymentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        ssm.StringParameter(self, 'LogicalId1', string_value='placeholder_value1')
        ssm.StringParameter(self, 'LogicalId2', string_value='placeholder_value2')


class DeploymentStage(Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        DeploymentStack(self, "TestDeploymentStack")


class TestStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pipeline = pipelines.CodePipeline(
            self, "Pipeline",
            self_mutation=False,
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.connection(
                    repo_string=f"{settings.git_repo_owner}/{settings.git_repo_name}",
                    branch=settings.git_repo_branch,
                    code_build_clone_output=True,
                    connection_arn=settings.codestar_connection,
                ),
                env={"GIT_TAG": settings.git_repo_tag},
                commands=[
                    "if [ -n \"$GIT_TAG\" ]; git checkout tags/$GIT_TAG; fi",
                    "npm install -g aws-cdk",
                    "pip install -r requirements.txt",
                    "cdk synth"
                ]),

        )
        pipeline.add_stage(DeploymentStage(self, 'Prod'))
