'''import os 
from bedrock_agentcore.runtime import BedrockAgentCoreApp 
from strands import Agent 
from strands.models import BedrockModel 
from strands.tools.mcp import MCPClient 
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client 

app = BedrockAgentCoreApp() 
GATEWAY_URL = os.environ.get("GATEWAY_URL", "") 
REGION = os.environ.get("AWS_REGION", "eu-south-2") 

modelo = BedrockModel( 
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0", 
    region_name=REGION, 
    ) 

mcp_client = MCPClient(
    lambda: aws_iam_streamablehttp_client( 
        endpoint=GATEWAY_URL, 
        aws_region=REGION, 
        aws_service="bedrock-agentcore", 
    )
) 

@app.entrypoint 
def invoke(payload): 
    
    mensaje = payload.get("prompt", "Hola") 
    
    with mcp_client: 
        tools = mcp_client.list_tools_sync() 
        agent = Agent(model=modelo, tools=tools) 
        resultado = agent(mensaje) 
    
    return {"respuesta": resultado.message} 

if __name__ == "__main__": 
    app.run()
    
    '''
    
import os
import traceback
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client

app = BedrockAgentCoreApp()

GATEWAY_URL = os.environ.get("GATEWAY_URL", "")
REGION = os.environ.get("AWS_REGION", "eu-south-2")

modelo = BedrockModel(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name=REGION,
)

mcp_client = MCPClient(lambda: aws_iam_streamablehttp_client(
    endpoint=GATEWAY_URL,
    aws_region=REGION,
    aws_service="bedrock-agentcore",
))

@app.entrypoint
def invoke(payload):
    try:
        mensaje = payload.get("prompt", "Hola")
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(model=modelo, tools=tools)
            resultado = agent(mensaje)
        return {"respuesta": resultado.message}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    app.run()