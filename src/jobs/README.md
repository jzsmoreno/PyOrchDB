# Azure Machine Learning
This folder contains the code to deploy a compute instance in [`Azure Machine Learning`](https://learn.microsoft.com/en-us/azure/machine-learning/overview-what-is-azure-machine-learning?view=azureml-api-2) using [`Azure CLI`](https://learn.microsoft.com/en-us/cli/azure/). Here below you can see the syntax of the command.

```powershell
az ml compute create -g <resource_group_name> -w <workspace_name> -f create-instance.yml
```

To run the `pipeline_job.yml` in the computer instance you just created, you need to run the following command.

```powershell
az ml job create -f pipeline_job.yml -g <resource_group_name> -w <workspace_name>
```

## Loading a serialized model in Azure ML Models

This section being an independent process of the ETL has its own `requirements.txt` file since it does not depend on the execution of the same. Therefore, if you have a serialized `.pkl` model and you want to deploy it to a workspace in [`Azure Machine Learning`](https://learn.microsoft.com/en-us/azure/machine-learning/concept-workspace?view=azureml-api-2), you must execute the following commands:
```powershell
az login
$subscription_id = (az account show --query 'id' --output tsv)
$resource_group_name = '<resource_group_name>'
$workspace_name = '<workspace_name>'
$model_name = 'models/<model_name>'
$environment_path = 'models/<conda.yaml>'
$input_example = 'models/<input_example.json>'
Start-Process python -ArgumentList './upload_model.py', $subscription_id, $resource_group_name, $workspace_name, $model_name, $environment_path, $input_example -NoNewWindow -Wait
```

This will create an endpoint to consume the model. 

# Local Azure Machine Learning Job

## Create a URL folder data asset

The supported paths you can use when creating a URI file data asset are:

- Local: A relative path from the source directory of the project that contains your local data folder (`source_directory`). For example, `./data/`
- Azure Blob Storage: `wasbs://<account_name>.blob.core.windows.net/<container_name>/<folder>/<file>`
- Azure Data Lake Storage (Gen 2): `abfss://<file_system>@<account_name>.dfs.core.windows.net/<folder>/<file>`
- Datastore: `azureml://datastores/<datastore_name>/paths/<folder>/<file>`

To create a URI file data asset, you can use the following code:

```python
from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes

my_path = '<supported-path>'

my_data = Data(
    path=my_path,
    type=AssetTypes.URI_FILE,
    description="<description>",
    name="<name>",
    version="<version>"
)

ml_client.data.create_or_update(my_data)
```

## Create a compute instance

You need a compute target to run your script in. If you don't have one already, you can create a new compute instance using this

```python
from azure.ai.ml.entities import ComputeInstance

ci_basic_name = "basic-ci-12345"
ci_basic = ComputeInstance(
    name=ci_basic_name, 
    size="STANDARD_DS3_v2"
)
ml_client.begin_create_or_update(ci_basic).result()
```