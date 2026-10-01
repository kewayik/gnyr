import aws_cdk as cdk 
from aws_cdk.assertions import Template 
from g_ny_r.g_ny_r_stack import GNyRStack 

def test_dynamodb_table_created(): 
    app = cdk.App() 
    stack = GNyRStack( 
        app, 
        "TestStack", 
        kb_id="dummy", 
        env=cdk.Environment(account="123456789012", region="eu-south-2"), 
    ) 
    template = Template.from_stack(stack) 
    template.resource_count_is("AWS::DynamoDB::Table", 1)