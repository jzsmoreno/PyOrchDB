az login
$resource_group_name = 'test'
$template_file = 'template.json'
$storage_account_name = 'testsablob01'
$sql_server_name = 'gentestsrv01'
$admin_username = 'SqlMainUser'
$admin_password = 'h0gr3wmK177d'
$database_name = 'testdbsrv01'

az deployment group create --resource-group $resource_group_name --template-file $template_file --parameters storageAccountName=$storage_account_name sqlServerName=$sql_server_name adminUsername=$admin_username adminPassword=$admin_password databaseName=$database_name
