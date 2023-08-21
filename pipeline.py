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
ps_command += "'Resource group already exists.'\n"
ps_command += "}\n"
ps_command += "else{\n\t"
ps_command += "echo "
ps_command += "'Resource group does not exist. Creating...'\n\t"
ps_command += f"az group create --name $resourceGroupName --location {yaml_data['location']}"
ps_command += "\n\t"
ps_command += f"az ml workspace create --resource-group {yaml_data['resource_group_name']}"
ps_command += f" --name {yaml_data['workspace_name']}"
ps_command += f" --location {yaml_data['location']}"
ps_command += "\n}\n"

py_command = "print('Hello World!')"


if __name__ == "__main__":
    # create run_workflow.py
    with open("run_workflow.py", "w") as file:
        file.write(py_command)

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
    ps_command += " --output tsv)\n"
    ps_command += "az storage blob upload --account-name "
    ps_command += f"$storageName --account-key $storageKey --container-name azureml "
    ps_command += f"--file ./{yaml_data['script_name']} --name {yaml_data['script_name']}"

    # save command_line into a run.ps1 file
    with open("run.ps1", "w") as file:
        file.write(ps_command)

    # run the PowerShell script from Python
    try:
        subprocess.run(ps_command, shell=True, check=True)
        print("PowerShell script executed successfully.")
    except subprocess.CalledProcessError as e:
        print("Error executing PowerShell script:", e)
