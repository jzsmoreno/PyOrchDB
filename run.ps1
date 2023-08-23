az login
$resourceGroupName='test'

if (az group exists --resource-group $resourceGroupName){
	echo 'Resource group already exists.'
	try{
		while ($true){
			az resource delete --name (az resource list --query '[0].{name:name}' --resource-group test --output table)[2] --resource-type (az resource list --query [0]'.{name:type}' --resource-group test --output table)[2] --resource-group test
			Start-Sleep -Seconds 1.5
		}	
	}
	catch{
		echo 'Resources removed.'
		az ml workspace create --resource-group test --name testazml --location eastus
	}
}
else{
	echo 'Resource group does not exist. Creating...'
	az group create --name $resourceGroupName --location eastus
	az ml workspace create --resource-group test --name testazml --location eastus
}
$storageName = (az ml datastore list --query '[0].{storageName:account_name}' --output table --workspace-name testazml --resource-group test)[2]
$storageKey = (az storage account keys list --resource-group test --account-name $storageName --query '[0].value' --output tsv)
az storage blob upload --account-name $storageName --account-key $storageKey --container-name azureml --file ./run_workflow.py --name run_workflow.py --overwrite
az ml job create --name test_pipeline --file ./jobs/experiment_job.yml --workspace-name testazml --resource-group test