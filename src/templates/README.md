# Azure Resource Manager template
This folder contains the templates for deploying the infrastructure in Azure using [`Azure CLI`](https://learn.microsoft.com/en-us/cli/azure/). Here in `run_template_infra.ps1` you can see the syntax of the command.

## Deployment

The creation of the infrastructure in `infra_template.json` can be easily created by executing the following command:
```powershell
.\run_template_infra.ps1
```

## Delete all resources in the resource group

If you want to delete all the _resources_ in the _resource group_. Execute the following command:
```powershell
.\delete_all_resources.ps1 '<resourceGroupName>'
```

It is necessary to modify the variable `<resourceGroupName>` by the name of the _resource group_ from which you want to delete the _resources_. 

We recommend if you want to work with the `pipeline.py` change the `delete_az_resources` variable to `True` (from the `config.yml` file) and run the `run.ps1` script. This will delete all resources in the `resource_group_name` resource group defined in the same `.yml` file. Since the `delete_all_resources.ps1` script by default only performs a soft deletion of the [`Azure Machine Learning`](https://learn.microsoft.com/en-us/azure/machine-learning/concept-workspace?view=azureml-api-2) workspace. On the other hand, to make sure that the resource has been deleted correctly, when executing the command `.delete_all_resources.ps1` it will be necessary to answer `y` to the option _permanently delete a workspace_.

## Creation of a database from an existing SQL server

In case you are using scenario 2 and you want to create a database over an existing [`SQL server`](https://learn.microsoft.com/en-us/azure/azure-sql/azure-sql-iaas-vs-paas-what-is-overview?view=azuresql), you will need to execute the following commands:
```powershell
az login
$resourceGroupName = '<resourceGroupName>'
$sql_server_name = '<sql-server-name>'
$database_name = '<database-name>'
az sql db create --resource-group $resourceGroupName --server $sql_server_name --name $database_name --service-objective GP_S_Gen5_1
```

Here are some examples of the `--service-objective` parameter: `Basic`, `S0`, `P1`, `GP_Gen4_1`, `GP_Gen5_S_8`, `BC_Gen5_2`, `HS_Gen5_32`. These follow the convention of specifying the purpose of the database followed by the number of cores.

## Creation of containers from an existing storage account

Within the [`ARM template`](https://learn.microsoft.com/en-us/azure/azure-resource-manager/templates/) in `templates` is the default creation of the `rawdata` and `processed` containers. But if you want to create the containers on an existing storage account, you need to execute the following commands:
```powershell
$storage_account_name = '<storage_account_name>'
az storage container create --name rawdata --account-name $storage_account_name
az storage container create --name processed --account-name $storage_account_name
```

## Manual infrastructure deployment

If you do not want to use _Azure Resource Manager_, you can run the following commands for the [`storage account`](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-overview):
```powershell
$storage_account_name = '<storage_account_name>'
$resourceGroupName = '<resourceGroupName>'
$location_name = '<location_name>'
az storage account create -n $storage_account_name -g $resourceGroupName --kind StorageV2 -l $location_name --sku Standard_LRS -t Account
az storage container create --name rawdata --account-name $storage_account_name
az storage container create --name processed --account-name $storage_account_name
az storage account hns-migration start --type upgrade -n $storage_account_name -g $resourceGroupName
```

Previous commands already include the upgrade with [`Azure Data Lake Gen2`](https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-best-practices) capabilities and the following are the commands for server creation:

```powershell
$sql_server_name = '<sql_server_name>'
$admin_username = '<admin_username>'
$admin_password = '<admin_password>' # It is recommended to store this password securely, for example using Azure Key Vault
az sql server create -l $location_name -g $resourceGroupName -n $sql_server_name -u $admin_username -p $admin_password -e false
```

  Some of the benefits of updating your storage account is that you can perform operations such as `create`, `show`, `file list`, `delete`, `directory create`, `directory show`, `directory move`, `directory delete` and `directory exists`. The first ones follow the following syntax and are instructions that are executed at the container level.

```powershell
az storage fs <action> -n <container name> --account-name $storage_account_name --auth-mode login
```
While the second ones prefixed with _directory_ are executed at the folder system level.
```powershell
az storage fs <action> -n <directory_name> -f <container name> --account-name $storage_account_name --auth-mode login
```

We also have file-level instructions such as `download`, `list`, `upload`, `show`, `move` and `delete`, the syntax used for _downloading_ and _uploading_ files is as follows:
```powershell
az storage fs file <action> -s '<local_path>' -p <cloud path> -f <container name> --account-name $storage_account_name --auth-mode login
```
The only difference is that for uploading the label will be `-s` while for downloading it will be `-d`. For the rest of the commands mentioned at the file level, the following syntax is used.

```powershell
az storage fs file <action> -p <file> -f <container name> --account-name $storage_account_name --auth-mode login
```
