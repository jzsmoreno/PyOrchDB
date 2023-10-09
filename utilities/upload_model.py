import os

from azureml.core import Environment, Model, Workspace
from azureml.core.webservice import AciWebservice


class UploadModelToML:
    """Performs the upload of a `serialized` Machine Learning model to `Azure ML`."""

    def __init__(self, subscription_id, resource_group, workspace_name):
        """Inputs required to create a connection to `Azure ML`"""
        self._subscription_id = subscription_id
        self._resource_group = resource_group
        self._workspace_name = workspace_name

    def upload_model(self, model_path, model_name):
        """Create a connection to the `azure ml` resource
        and to load the model you need to add the path and name of your model."""
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


if __name__ == "__main__":
    subscription_id = "<suscription_id>"
    resource_group = "<resource_group_name>"
    workspace_name = "<workspace_name>"
    model_name = "<model_name>"

    # Gets the absolute path of the .pkl model relative to the script
    model_path = os.path.join(os.path.dirname(__file__), model_name + ".pkl")

    azureml_controller = UploadModelToML(subscription_id, resource_group, workspace_name)
    azureml_controller.upload_model(model_name=model_name, model_path=model_path)
