import os
from azureml.core import Workspace, Model, Environment
from azureml.core.webservice import AciWebservice

class UploadModelToML:
    
    def __init__(self, subscription_id,resource_group, workspace_name):
        '''Necesaty inputs to create a conexion with Azure ML'''
        self._subscription_id = subscription_id
        self._resource_group = resource_group
        self._workspace_name = workspace_name

    def upload_model(self, model_path,model_name):
        '''Create a conexion with the resource of azure ml
        and to upload the model you need to add the path and name of your model.'''
        try:
            ws = Workspace(subscription_id=self._subscription_id, resource_group=self._resource_group, workspace_name=self._workspace_name)            
            print("Conexión exitosa con Azure Machine Learning.")           
            modelo_cargado = Model.register(
                workspace=ws,
                model_path=model_path,
                model_name=model_name,
                tags={'tipo': 'pkl'}
            )
            print("Modelo .pkl registrado con éxito en Azure Machine Learning.")
        except Exception as e:
            print(f"Error al conectar con Azure Machine Learning: {str(e)}")

