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
.\delete_all_resources.ps1
```

It is necessary to modify the variable `$resourceGroupName` by the name of the _resource group_ from which you want to delete the _resources_.