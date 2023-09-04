param([string] $resourceGroupName)
az login

if (az group exists --resource-group $resourceGroupName){
	echo 'Resource group already exists.'
	$mode = read-host "Do you want to try to permanently delete a workspace? [y/n]"
	if ($mode.Contains("y")){
		try{
			$workspaceName = read-host "Enter the workspace name (Azure ML)"
			az ml workspace delete --resource-group $resourceGroupName --name $workspaceName --permanently-delete -y
			echo 'Workspace successfully deleted'
		}
		catch{
			continue
		}
	}
	try{
		while ($true){
			$resourceName = (az resource list --query '[0].{name:name}' --resource-group $resourceGroupName --output table)[2]
			az resource delete --name $resourceName --resource-type (az resource list --query [0]'.{name:type}' --resource-group $resourceGroupName --output table)[2] --resource-group $resourceGroupName
			Start-Sleep -Seconds 1.5
			echo "Resource $resourceName removed."
		}		
	}
	catch{
		echo 'All resources removed.'
	}
}