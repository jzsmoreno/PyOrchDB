az login
$resource_group_name = 'test'
$location_name = 'eastus'
$template_file = 'template.json'
$storage_account_name = 'testsablob01'
$sql_server_name = 'gentestsrv01'
$admin_username = 'SqlMainUser'
$admin_password = 'h0gr3wmK177d'
$database_name = 'testdbsrv01'

if (az group exists --resource-group $resource_group_name){
    echo 'Resource group already exists. Building resources...'
}
else{
    echo 'Resource group does not exist. Creating...'
	az group create --name $resourceGroupName --location $location_name
}

echo 'Deploying resources...'
az deployment group create --resource-group $resource_group_name --template-file $template_file --parameters storageAccountName=$storage_account_name sqlServerName=$sql_server_name adminUsername=$admin_username adminPassword=$admin_password databaseName=$database_name
$storageBlob_conn = (az storage account show-connection-string --name $storage_account_name --resource-group $resource_group_name --query 'connectionString' --output tsv)