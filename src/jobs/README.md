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