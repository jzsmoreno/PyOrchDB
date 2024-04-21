# Azure Machine Learning
This folder contains the code to deploy a compute instance in [`Azure Machine Learning`](https://learn.microsoft.com/en-us/azure/machine-learning/overview-what-is-azure-machine-learning?view=azureml-api-2) using [`Azure CLI`](https://learn.microsoft.com/en-us/cli/azure/). Here below you can see the syntax of the command.

```powershell
az ml compute create -g <resource_group_name> -w <workspace_name> -f create-instance.yml
```

To run the `pipeline_job.yml` or `experiment_job.yml` in the computer instance you just created, you need to run the following command.

```powershell
az ml job create -f pipeline_job.yml -g <resource_group_name> -w <workspace_name>
```

## Loading a serialized model in Azure ML Models

This section is a separate process from the ETL, so it has its own `requirements.txt` file since it does not depend on the execution of the previous one. Therefore, if you have a serialized `.pkl` model and you want to deploy it to a workspace in [`Azure Machine Learning`](https://learn.microsoft.com/en-us/azure/machine-learning/concept-workspace?view=azureml-api-2), you must execute the following commands:
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

## Create a URI folder data asset

The supported paths you can use when creating a URI file data asset are:

- Local: A relative path from the source directory of the project that contains your local data folder (`source_directory`). For example, `./data/`
- Azure Blob Storage: `wasbs://<account_name>.blob.core.windows.net/<container_name>/<folder>/<file>`
- Azure Data Lake Storage (Gen 2): `abfss://<file_system>@<account_name>.dfs.core.windows.net/<folder>/<file>`
- Datastore: `azureml://datastores/<datastore_name>/paths/<folder>/<file>`

To create a URI file data asset, you can use the following code:

```python
from azure.ai.ml import MLClient, command
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import AmlCompute, ComputeInstance, Data
from azure.identity import DefaultAzureCredential

# authenticate
credential = DefaultAzureCredential()

# Get a handle to the workspace
self.ml_client = MLClient(
    credential=credential,
    subscription_id="<subscription-id>",
    resource_group_name="<rg-name>",
    workspace_name="<ws-name>",
)

my_path = "<supported-path>"

my_data = Data(
    path=my_path,
    type=AssetTypes.URI_FILE,
    description="<description>",
    name="<name>",
    version="<version>",
)

ml_client.data.create_or_update(my_data)
```

## Create a compute instance

You need a compute target to run your script in. If you don't have one already, you can create a new compute instance using this

```python
ci_basic_name = "basic-ci"
ci_basic = ComputeInstance(name=ci_basic_name, size="STANDARD_DS3_v2")
ml_client.begin_create_or_update(ci_basic).result()
```

When you run a script, you will want to use a computational target that is scalable, so you can use a computational cluster.

## Create a compute cluster

You can create a compute cluster using the following code:

```python
cluster_basic = AmlCompute(
    name="cpu-cluster",
    type="amlcompute",
    size="STANDARD_DS3_v2",
    location="westus",
    min_instances=0,
    max_instances=2,
    idle_time_before_scale_down=120,
    tier="low_priority",
)
ml_client.begin_create_or_update(cluster_basic).result()
```

## Use a compute cluster

You can use a compute cluster to run your script.

```python
# configure job
job = command(
    code="./",
    command="python job_workflow.py",
    environment="AzureML-sklearn-0.24-ubuntu18.04-py37-cpu@latest",
    compute="cpu-cluster",
    display_name="train-with-cluster",
    experiment_name="training",
)

# submit job
returned_job = ml_client.create_or_update(job)
aml_url = returned_job.studio_url
print("Monitor your job at", aml_url)
```
you can also see the [`Pipeline documentation`](https://learn.microsoft.com/es-es/training/modules/run-pipelines-azure-machine-learning/3-create-pipeline) for more details.
## Configure and run a sweep job

To prepare the sweep job, you must first create a base command job. 

```python
# configure command job as base
job = command(
    code="./",
    command="python job_workflow.py --regularization ${{inputs.reg_rate}}",
    inputs={
        "reg_rate": 0.01,
    },
    environment="AzureML-sklearn-0.24-ubuntu18.04-py37-cpu@latest",
    compute="aml-cluster",
)

command_job_for_sweep = job(
    reg_rate=Normal(mu=0.5, sigma=0.01),
)

# apply the sweep parameter to obtain the sweep_job
sweep_job = command_job_for_sweep.sweep(
    compute="aml-cluster",
    sampling_algorithm="random",
    primary_metric="Accuracy",
    goal="Maximize",
)

# set the name of the sweep job experiment
sweep_job.experiment_name = "sweep-example"

# define the limits for this sweep
sweep_job.set_limits(max_total_trials=4, max_concurrent_trials=2, timeout=7200)

# submit the sweep
returned_sweep_job = ml_client.create_or_update(sweep_job)
```
# Create a MLTable data asset 

A MLTable data asset allows you to point to tabular data. You must have the `mltable` [`Python SDK`](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-mltable?view=azureml-api-2&tabs=cli) and `pandas` installed in your Python environment, with this command:

```bash
pip install -U mltable azureml-dataprep[pandas]
```
To create a MLTable data asset, you can use the `from_parquet_files` method.
```python
import mltable

# glob the parquet file paths.
paths = [
    {
        "pattern": "wasbs://<account_name>.blob.core.windows.net/<container_name>/<folder>/<file>.parquet"
    },
]

# create a table from the parquet paths
tbl = mltable.from_parquet_files(paths)
df = tbl.to_pandas_dataframe()
```
you can also see the [`MLTable documentation`](https://learn.microsoft.com/en-us/training/modules/make-data-available-azure-machine-learning/4-create-data-asset) for more information.