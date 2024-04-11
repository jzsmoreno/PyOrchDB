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


ci_basic_name = "basic-ci-12345"
ci_basic = ComputeInstance(name=ci_basic_name, size="STANDARD_DS3_v2")
ml_client.begin_create_or_update(ci_basic).result()


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

# configure job
job = command(
    code="./",
    command="python job_workflow.py",
    environment="AzureML-sklearn-0.24-ubuntu18.04-py37-cpu@latest",
    compute="cpu-cluster",
    display_name="train-with-cluster",
    experiment_name="diabetes-training",
)

# submit job
returned_job = ml_client.create_or_update(job)
aml_url = returned_job.studio_url
print("Monitor your job at", aml_url)
