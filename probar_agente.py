import boto3
import json
from botocore.config import Config

client = boto3.client(
    'bedrock-agentcore',
    region_name='eu-south-2',
    config=Config(connect_timeout=10, read_timeout=900),
)

ARN = 'arn:aws:bedrock-agentcore:eu-south-2:905223168643:runtime/agente_gnyrV2-u4Ffwy7wPw'

def preguntar(prompt):
    try:
        respuesta = client.invoke_agent_runtime(
            agentRuntimeArn=ARN,
            payload=json.dumps({'prompt': prompt}).encode(),
            qualifier='DEFAULT'
        )
        print(respuesta['response'].read().decode())
    except Exception as e:
        print('ERROR:', e.response)
    print('---')

preguntar('Añade huevos a la nevera, cantidad 6')
preguntar('Que tengo en la nevera?')
preguntar('Dame una receta con lo que tengo en la nevera, consultando el libro de recetas')