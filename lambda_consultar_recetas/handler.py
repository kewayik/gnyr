import os

import boto3


bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")


def lambda_handler(event, context):
	pregunta = event.get("pregunta", "")
	respuesta = bedrock_agent_runtime.retrieve(
		knowledgeBaseId=os.environ["KB_ID"],
		retrievalQuery={"text": pregunta},
	)
	fragmentos = [
		resultado["content"]["text"]
		for resultado in respuesta.get("retrievalResults", [])
	]
	return {"status": "ok", "fragmentos_relevantes": fragmentos}