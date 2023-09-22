# pipeline for run script.py in AzureML
import subprocess

import yaml

yaml_file_path = "./config.yml"

with open(yaml_file_path, "r") as yaml_file:
    yaml_data = yaml.safe_load(yaml_file)

print(yaml_data)

# creation of run.ps1 file to execute
ps_command = "az login\n"
ps_command += f"$resourceGroupName='{yaml_data['resource_group_name']}'"
ps_command += "\n"
ps_command += "\n"
ps_command += "if (az group exists --resource-group $resourceGroupName){\n"
ps_command += "\techo "
ps_command += "'Resource group already exists.'\n\t"
ps_command += f"if (${yaml_data['delete_az_resources']})"
ps_command += "{\n\t\ttry{\n\t\t\t"
ps_command += f"az ml workspace delete --resource-group {yaml_data['resource_group_name']} "
ps_command += f"--name {yaml_data['workspace_name']} --permanently-delete -y"
ps_command += "\n\t\t}\t\t\n"
ps_command += "\t\tcatch{\n\t"
ps_command += "\t\t continue"
ps_command += "\n\t\t}\n"
ps_command += "\n\t\ttry{\n"
ps_command += "\t\t\twhile ($true){\n\t\t\t\t"
ps_command += "az resource delete --name (az resource list --query '[0].{name:name}' "
ps_command += f"--resource-group {yaml_data['resource_group_name']} --output table)[2] "
ps_command += "--resource-type (az resource list --query [0]'.{name:type}' "
ps_command += f"--resource-group {yaml_data['resource_group_name']} --output table)[2] "
ps_command += f"--resource-group {yaml_data['resource_group_name']}"
ps_command += "\n\t\t\t\tStart-Sleep -Seconds 1.5"
ps_command += "\n\t\t\t}\t\t"
ps_command += "\n\t\t}\n"
ps_command += "\t\tcatch{\n\t"
ps_command += "\t\t"
ps_command += "echo 'Resources removed.'\n\t\t\t"
ps_command += "echo 'Creating a new workspace...'\n\t\t\t"
ps_command += f"az ml workspace create --resource-group {yaml_data['resource_group_name']}"
ps_command += f" --name {yaml_data['workspace_name']}"
ps_command += f" --location {yaml_data['location']}"
ps_command += "\n\t\t}\n"
ps_command += "\t}\n}\n"
ps_command += "else{\n\t"
ps_command += "echo "
ps_command += "'Resource group does not exist. Creating...'\n\t"
ps_command += f"az group create --name $resourceGroupName --location {yaml_data['location']}"
ps_command += "\n\t"
ps_command += f"az ml workspace create --resource-group {yaml_data['resource_group_name']}"
ps_command += f" --name {yaml_data['workspace_name']}"
ps_command += f" --location {yaml_data['location']}"
ps_command += "\n}\n"
ps_command += "try{\n\t"
ps_command += f"az ml workspace create --resource-group {yaml_data['resource_group_name']}"
ps_command += f" --name {yaml_data['workspace_name']}"
ps_command += f" --location {yaml_data['location']}"
ps_command += "\n}\ncatch{\n\tcontinue\n}\n"
ps_command += f"az ml compute create -g {yaml_data['resource_group_name']} "
ps_command += f"-w {yaml_data['workspace_name']} -f {yaml_data['instance_file']}"
ps_command += "\n"


if __name__ == "__main__":
    # execute run_workflow.py to transform the data
    ps_command += "echo 'Extraction and transformation. Running...'\n"
    ps_command += "$storageBlob_conn = (az storage account show-connection-string "
    ps_command += f"--name {yaml_data['storage_account_name']} "
    ps_command += f"--resource-group {yaml_data['sa_resource_group_name']} --query 'connectionString' --output tsv)"
    ps_command += "\n"
    ps_command += f"$db_conn_string = (az sql db show-connection-string -c odbc -n {yaml_data['database_name']} -s "
    ps_command += f"{yaml_data['sql_server_name']} -a Sqlpassword --output tsv)"
    ps_command += "\n"
    ps_command += f"Start-Process python -ArgumentList './{yaml_data['script_name']}', '{yaml_data['storage_account_name']}', "
    ps_command += f"$storageBlob_conn, '{yaml_data['sa_container_name']}', '{yaml_data['sa_resource_group_name']}', "
    ps_command += f"'{yaml_data['exclude_files']}', '{yaml_data['sa_container_directory']}', $db_conn_string -NoNewWindow -Wait"
    ps_command += "\n"
    # get storage account name
    ps_command += "$storageName = (az ml datastore list --query '[0].{storageName:account_name}' "
    ps_command += "--output table "
    ps_command += f"--workspace-name {yaml_data['workspace_name']} "
    ps_command += f"--resource-group {yaml_data['resource_group_name']})[2]"
    # get storage account key
    ps_command += "\n"
    ps_command += "$storageKey = (az storage account keys list --resource-group "
    ps_command += (
        f"{yaml_data['resource_group_name']} --account-name $storageName --query '[0].value'"
    )
    # create a job in the workspace
    ps_command += " --output tsv)\n"
    ps_command += "az storage blob upload --account-name "
    ps_command += f"$storageName --account-key $storageKey --container-name azureml "
    ps_command += f"--file ./jobs/{yaml_data['job_script']} --name {yaml_data['job_script']}"
    ps_command += " --overwrite\n"
    ps_command += f"az ml job create -f {yaml_data['job_file']} "
    ps_command += f"-w {yaml_data['workspace_name']} "
    ps_command += f"-g {yaml_data['resource_group_name']}"
    ps_command += "\n"

    # save command_line into a run.ps1 file
    with open("run.ps1", "w") as file:
        file.write(ps_command)

    # run the PowerShell script from Python
    try:
        # subprocess.run(ps_command, shell=True, check=True)
        print("PowerShell script executed successfully.")
    except subprocess.CalledProcessError as e:
        print("Error executing PowerShell script:", e)
