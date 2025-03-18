import json
import logging
import os
from io import StringIO

import mlflow
import numpy as np
from mlflow.pyfunc.scoring_server import infer_and_parse_json_input, predictions_to_json


def init():
    """
    This function is called when the container is initialized/started, typically after create/update of the deployment.
    You can write the logic here to perform init operations like caching the model in memory
    """
    global model
    global input_schema
    # AZUREML_MODEL_DIR is an environment variable created during deployment.
    # It is the path to the model folder (./azureml-models/$MODEL_NAME/$VERSION)
    # Please provide your model's folder name if there is one
    model_path = os.path.join(os.getenv("AZUREML_MODEL_DIR"), "model_clf")
    # Load the TensorFlow model from the MLflow model path
    model = mlflow.tensorflow.load_model(model_path)
    input_schema = model.metadata.get_input_schema()
    logging.info("Model loaded successfully.")


def run(raw_data):
    """
    This function is called for every invocation of the endpoint to perform the actual scoring/prediction.
    In the example we extract the data from the json input and call the TensorFlow model's predict method
    and return the result back.
    """
    logging.info("Request received.")

    # Parse the incoming request data
    json_data = json.loads(raw_data)
    if "input_data" not in json_data.keys():
        raise Exception("Request must contain a top level key named 'input_data'")

    serving_input = json.dumps(json_data["input_data"])
    data = infer_and_parse_json_input(serving_input, input_schema)
    data = np.array(data)  # Ensure the input is in numpy format

    # Perform prediction using the loaded TensorFlow model
    predictions = model.predict(data)

    logging.info("Request processed successfully.")

    result = StringIO()
    predictions_to_json(predictions, result)
    return result.getvalue()
