import aws_cdk as core
import aws_cdk.assertions as assertions

from g_ny_r.g_ny_r_stack import GNyRStack

# example tests. To run these tests, uncomment this file along with the example
# resource in g_ny_r/g_ny_r_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = GNyRStack(app, "g-ny-r")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
