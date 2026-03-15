import boto3

'''
client = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1"
)

print("AWS Bedrock conectado")
'''


bedrock = boto3.client("bedrock")

response = bedrock.list_foundation_models()

for model in response["modelSummaries"]:
    print(model["modelId"])