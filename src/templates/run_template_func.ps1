$mode = read-host "Do you want to use the default values? [y/n]"
if ($mode.Contains("y"))
{
    $resource_group_name = 'test'
    $location_name = 'eastus'
    if (((Get-Location).Path).Contains("templates")){
        $template_file = 'func_template.json'
    }
    else{
        $template_file = './templates/func_template.json'
    }
    $appServicePlanName = 'myASPlan'
    $appServiceName = 'myAppS-development'
    $containerRegistryName = 'myCRegistryDev'
    $appFunctionName = 'AzFLabDev'
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
    $template_file = read-host "Enter template file path"
    if ($template_file.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        if (((Get-Location).Path).Contains("templates")){
            $template_file = 'func_template.json'
        }
        else{
            $template_file = './templates/func_template.json'
        }
    }
    $appServicePlanName = read-host "Enter App Service Plan name (example: myASPlan)"
    if ($appServicePlanName.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        $appServicePlanName = 'myASPlan'
    }
    $appServiceName = read-host "Enter App Service name (example: myAppS-development)"
    if ($appServiceName.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        $appServiceName = 'myAppS-development'
    }
    $containerRegistryName = read-host "Enter Container Registry name (example: myCRegistryDev)"
    if ($containerRegistryName.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        $containerRegistryName = 'myCRegistryDev'
    }
    $appFunctionName = read-host "Enter Function name (example: AzFLabDev)"
    if ($appFunctionName.Length -gt 0){
        Write-Output 'Variable defined'
    }
    else{
        Write-Output 'Invalid entry : Using default value'
        $appFunctionName = 'AzFLabDev'
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
    az deployment group create --resource-group $resource_group_name --template-file $template_file --parameters appServicePlanName=$appServicePlanName appServiceName=$appServiceName containerRegistryName=$containerRegistryName appFunctionName=$appFunctionName
}
catch{
    Write-Output 'It was not possible to create the resources, check the resource group or the input parameters.'
}