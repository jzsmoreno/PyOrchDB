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
ps_command += "'Resource group $resourceGroupName already exists.'\n"
ps_command += "}\n"
ps_command += "else{\n\t"
ps_command += "echo "
ps_command += "'Resource group $resourceGroupName does not exist. Creating...'\n\t"
ps_command += f"az group create --name $resourceGroupName --location {yaml_data['location']}"
ps_command += "\n\t"
ps_command += f"az ml workspace create --resource-group {yaml_data['resource_group_name']}"
ps_command += f" --name {yaml_data['workspace_name']}"
ps_command += f" --location {yaml_data['location']}"
ps_command += "\n}"


if __name__ == "__main__":
    # save command_line into a run.ps1 file
    with open("run.ps1", "w") as file:
        file.write(ps_command)

    # run the PowerShell script from Python
    try:
        subprocess.run(ps_command, shell=True, check=True)
        print("PowerShell script executed successfully.")
    except subprocess.CalledProcessError as e:
        print("Error executing PowerShell script:", e)
