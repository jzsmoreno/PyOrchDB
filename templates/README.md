# Azure Resource Manager template
This folder contains the templates for deploying the infrastructure in Azure using [`Azure CLI`](https://learn.microsoft.com/en-us/cli/azure/). Here in `run_template.ps1` you can see the syntax of the command.

## Deployment

The creation of the infrastructure in `template.json` can be easily created by executing the following command:
```powershell
.\run_template.ps1
```

## Delete all resources in the resource group

If you want to delete all the _resources_ in the _resource group_. Execute the following command:
```powershell
.\delete_all_resources.ps1 '<resourceGroupName>'
```

It is necessary to modify the variable `<resourceGroupName>` by the name of the _resource group_ from which you want to delete the _resources_. 

We recommend if you want to work with the `pipeline.py` change the `delete_az_resources` variable to `True` (from the `config.yml` file) and run the `run.ps1` script. This will delete all resources in the `resource_group_name` resource group defined in the same `.yml` file. Since the `delete_all_resources.ps1` script by default only performs a soft deletion of the [`Azure Machine Learning`](https://learn.microsoft.com/en-us/azure/machine-learning/concept-workspace?view=azureml-api-2) workspace. On the other hand, to make sure that the resource has been deleted correctly, when executing the command `.delete_all_resources.ps1` it will be necessary to answer `y` to the option _permanently delete a workspace_.