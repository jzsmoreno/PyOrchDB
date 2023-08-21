az login
$resourceGroupName='test'

if (az group exists --resource-group $resourceGroupName){
	echo 'Resource group $resourceGroupName already exists.'
}
else{
	echo 'Resource group $resourceGroupName does not exist. Creating...'
	az group create --name $resourceGroupName --location eastus
	az ml workspace create --resource-group test --name testazml --location eastus
}