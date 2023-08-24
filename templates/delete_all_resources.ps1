az login
$resourceGroupName='test'

if (az group exists --resource-group $resourceGroupName){
	echo 'Resource group already exists.'
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