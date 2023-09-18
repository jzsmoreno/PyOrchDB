# Azure Machine Learning
This folder contains the code to deploy a compute instance in [`Azure Machine Learning`](https://learn.microsoft.com/en-us/azure/machine-learning/overview-what-is-azure-machine-learning?view=azureml-api-2) using [`Azure CLI`](https://learn.microsoft.com/en-us/cli/azure/). Here below you can see the syntax of the command.

```powershell
az ml compute create -g <resource_group_name> -w <workspace_name> -f create-instance.yml
```

To run the `pipeline_job.yml` in the computer instance you just created, you need to run the following command.

```powershell
az ml job create -f pipeline_job.yml -g <resource_group_name> -w <workspace_name>
```