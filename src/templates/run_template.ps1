az login
$mode = read-host "Do you want to use the default values? [y/n]"
if ($mode.Contains("y"))
{
    $resource_group_name = 'test'
    $location_name = 'eastus'
    if (((Get-Location).Path).Contains("templates")){
        $template_file = 'template.json'
    }
    else{
        $template_file = './templates/template.json'
    }
    $storage_account_name = 'testsablob01'
    $sql_server_name = 'gentestsrv01'
    $database_name = 'testdbsrv01'
    $admin_username = 'SqlMainUser'
    $admin_password = 'h0gr3wmK177d'
}
else{
    $resource_group_name = read-host "Enter group name (example: test)"
    if ($resource_group_name.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Using default value'
        $resource_group_name = 'test'
    }
    $location_name = read-host "Enter location name (example: eastus)"
    if ($location_name.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        $location_name = 'eastus'
    }
    $template_file = read-host "Enter template file path"
    if ($template_file.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        if (((Get-Location).Path).Contains("templates")){
            $template_file = 'template.json'
        }
        else{
            $template_file = './templates/template.json'
        }
    }
    $storage_account_name = read-host "Enter storage account name (example: testsablob01)"
    if ($storage_account_name.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        $storage_account_name = 'testsablob01'
    }
    $sql_server_name = read-host "Enter SQL Server name (example: gentestsrv01)"
    if ($sql_server_name.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        $sql_server_name = 'gentestsrv01'
    }
    $database_name = read-host "Enter database name (example: testdbsrv01)"
    if ($database_name.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        $database_name = 'testdbsrv01'
    }
    $admin_username = read-host "Enter database username for user admin"
    if ($admin_username.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        $admin_username = 'SqlMainUser'
    }
    $admin_password = read-host "Enter database password for user admin"
    if ($admin_password.Length -gt 8){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        $admin_password = 'h0gr3wmK177d'
    }
}

if (az group exists --resource-group $resource_group_name){
    Write-Output 'Resource group already exists. Building resources...'
}
else{
    Write-Output 'Resource group does not exist. Creating...'
	az group create --name $resourceGroupName --location $location_name
}

Write-Output 'Deploying resources...'
try{
    az deployment group create --resource-group $resource_group_name --template-file $template_file --parameters storageAccountName=$storage_account_name sqlServerName=$sql_server_name adminUsername=$admin_username adminPassword=$admin_password databaseName=$database_name
    $storageBlob_conn = (az storage account show-connection-string --name $storage_account_name --resource-group $resource_group_name --query 'connectionString' --output tsv)
    az storage container create --name rawdata --account-name $storage_account_name
    az storage container create --name processed --account-name $storage_account_name
}
catch{
    Write-Output 'It was not possible to create the resources, check the resource group or the input parameters.'
}