import os
import sys
import uuid

from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    CodeConfiguration,
    Environment,
    ManagedOnlineDeployment,
    ManagedOnlineEndpoint,
)
from azure.identity import DefaultAzureCredential
from azureml.core import Model, Workspace


class UploadModelToML:
    """Performs the upload of a `serialized` Machine Learning model to `Azure ML`."""

    def __init__(self, subscription_id: str, resource_group: str, workspace_name: str) -> None:
        """Inputs required to create a connection to `Azure ML`"""
        self._subscription_id = subscription_id
        self._resource_group = resource_group
        self._workspace_name = workspace_name

    def upload_model(self, model_path: str, model_name: str) -> None:
        """Create a connection to the `azure ml` resource
        and to load the model you need to add the path and name of your model."""
        self._model_name = model_name
        try:
            workspace = Workspace(
                subscription_id=self._subscription_id,
                resource_group=self._resource_group,
                workspace_name=self._workspace_name,
            )
            print("Successful connection to Azure Machine Learning.")
            loaded_model = Model.register(
                workspace=workspace,
                model_path=model_path,
                model_name=model_name,
                tags={"type": "pkl"},
            )
            print(".pkl model successfully registered in Azure Machine Learning.")
        except Exception as e:
            print(f"Error connecting to Azure Machine Learning: {str(e)}")

    def create_endpoint(self) -> None:
        # authenticate
        credential = DefaultAzureCredential()

        # Get a handle to the workspace
        self.ml_client = MLClient(
            credential=credential,
            subscription_id=self._subscription_id,
            resource_group_name=self._resource_group,
            workspace_name=self._workspace_name,
        )
        # Create a unique name for the endpoint
        self.online_endpoint_name = "model-endpoint-" + str(uuid.uuid4())[:8]
        # define an online endpoint
        endpoint = ManagedOnlineEndpoint(
            name=self.online_endpoint_name,
            description="this is an online endpoint",
            auth_mode="key",
            tags={
                "training_dataset": "model_defaults",
            },
        )
        endpoint = self.ml_client.online_endpoints.begin_create_or_update(endpoint).result()
        self.endpoint = self.ml_client.online_endpoints.get(name=self.online_endpoint_name)

        print(
            f'Endpoint "{self.endpoint.name}" with provisioning state "{self.endpoint.provisioning_state}" is retrieved'
        )

    def deploy_model(
        self,
        environment: str | Environment | None = None,
        model_name: str = None,
        custom: bool = True,
        **kwargs,
    ) -> None:
        """You can use an environment : `AzureML-sklearn-1.0-ubuntu20.04-py38-cpu:1`"""
        image = (
            kwargs["image"]
            if "image" in kwargs
            else "mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest"
        )
        instance_type = kwargs["instance_type"] if "instance_type" in kwargs else "Standard_D2as_v4"
        self.blue_deployment_name = (
            kwargs["blue_deployment_name"] if "blue_deployment_name" in kwargs else "blue"
        )
        # Choose the latest version of our registered model for deployment
        if model_name != None:
            self._model_name = model_name
        latest_model_version = max(
            [int(m.version) for m in self.ml_client.models.list(name=self._model_name)]
        )
        model = self.ml_client.models.get(name=self._model_name, version=latest_model_version)
        deployment_name = (
            kwargs["deployment_name"] if "deployment_name" in kwargs else "deployment-environment"
        )
        if isinstance(environment, str) and custom:
            if (environment.lower()).startswith("azureml") == -1 and environment.endswith(".pkl"):
                environment = Environment(
                    conda_file=environment,
                    image=image,
                    name=deployment_name,
                )
                self.ml_client.environments.create_or_update(environment)

        # Learn more on https://azure.microsoft.com/en-us/pricing/details/machine-learning/.
        blue_deployment = ManagedOnlineDeployment(
            name=self.blue_deployment_name,
            endpoint_name=self.online_endpoint_name,
            model=model,
            environment=environment,
            code_configuration=CodeConfiguration(code="./models", scoring_script="score.py"),
            instance_type=instance_type,
            instance_count=1,
        )

        # create the online deployment
        blue_deployment = self.ml_client.online_deployments.begin_create_or_update(
            blue_deployment
        ).result()

        # expect the deployment to take approximately 8 to 10 minutes.
        # blue deployment takes 100% traffic
        self.endpoint.traffic = {"blue": 100}
        self.ml_client.online_endpoints.begin_create_or_update(self.endpoint).result()
        # return an object that contains metadata for the endpoint
        endpoint = self.ml_client.online_endpoints.get(name=self.online_endpoint_name)

        # print a selection of the endpoint's metadata
        print(
            f"Name: {endpoint.name}\nStatus: {endpoint.provisioning_state}\nDescription: {endpoint.description}"
        )

    def test_endpoint(
        self,
        request_file: str = "./models/input_example.json",
        blue_deployment_name: str = None,
        online_endpoint_name: str = "blue",
    ):
        if isinstance(blue_deployment_name, str):
            self.blue_deployment_name = blue_deployment_name
            self.online_endpoint_name = online_endpoint_name
            credential = DefaultAzureCredential()

            self.ml_client = MLClient(
                credential=credential,
                subscription_id=self._subscription_id,
                resource_group_name=self._resource_group,
                workspace_name=self._workspace_name,
            )
        self.ml_client.online_endpoints.invoke(
            endpoint_name=self.online_endpoint_name,
            deployment_name=self.blue_deployment_name,
            request_file=request_file,
        )
        logs = self.ml_client.online_deployments.get_logs(
            name=self.blue_deployment_name, endpoint_name=self.online_endpoint_name, lines=50
        )
        print(logs)


if __name__ == "__main__":
    subscription_id = sys.argv[1]
    resource_group_name = sys.argv[2]
    workspace_name = sys.argv[3]
    model_name = sys.argv[4]
    environment_path = sys.argv[5]
    input_example = sys.argv[6]

    # Gets the absolute path of the .pkl model relative to the script
    model_path = os.path.join(os.path.dirname(__file__), model_name + ".pkl")
    model_name = model_name.split("/")[-1]

    print("Uploading the model to Azure ML Models...")
    azureml_controller = UploadModelToML(subscription_id, resource_group_name, workspace_name)
    azureml_controller.upload_model(model_name=model_name, model_path=model_path)

    print("Creating endpoint for model deployment...")
    azureml_controller.create_endpoint()

    print("Deploying the model...")
    azureml_controller.deploy_model(environment_path)

    print("Model deployed successfully")

    print("Testing the model deployment")
    azureml_controller.test_endpoint(input_example)
