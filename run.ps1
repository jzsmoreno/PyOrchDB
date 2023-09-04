az login
$resourceGroupName='test'

if (az group exists --resource-group $resourceGroupName){
	echo 'Resource group already exists.'
	if ($False){
		try{
			az ml workspace delete --resource-group test --name testazml --permanently-delete -y
		}		
		catch{
			 continue
		}

		try{
			while ($true){
				az resource delete --name (az resource list --query '[0].{name:name}' --resource-group test --output table)[2] --resource-type (az resource list --query [0]'.{name:type}' --resource-group test --output table)[2] --resource-group test
				Start-Sleep -Seconds 1.5
			}		
		}
		catch{
			echo 'Resources removed.'
			echo 'Creating a new workspace...'
			az ml workspace create --resource-group test --name testazml --location eastus
		}
	}
}
else{
	echo 'Resource group does not exist. Creating...'
	az group create --name $resourceGroupName --location eastus
	az ml workspace create --resource-group test --name testazml --location eastus
}
try{
	az ml workspace create --resource-group test --name testazml --location eastus
}
catch{
	continue
}
echo 'Extraction and transformation. Running...'
$storageBlob_conn = (az storage account show-connection-string --name testsa --resource-group test --query 'connectionString' --output tsv)
Start-Process python -ArgumentList './run_workflow.py', 'testsa', $storageBlob_conn, 'rawdata', 'test', 'catalog', '/' -NoNewWindow -Wait
$storageName = (az ml datastore list --query '[0].{storageName:account_name}' --output table --workspace-name testazml --resource-group test)[2]
$storageKey = (az storage account keys list --resource-group test --account-name $storageName --query '[0].value' --output tsv)
az storage blob upload --account-name $storageName --account-key $storageKey --container-name azureml --file ./jobs/job_workflow.py --name job_workflow.py --overwrite
az ml job create --name test_pipeline --file ./jobs/experiment_job.yml --workspace-name testazml --resource-group test
