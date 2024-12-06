# https://learn.microsoft.com/en-us/graph/api/chat-post?view=graph-rest-1.0&tabs=python

import argparse
import asyncio
import yaml
from azure.identity import DeviceCodeCredential
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.chat import Chat
from msgraph.generated.models.chat_type import ChatType
from msgraph.generated.models.conversation_member import ConversationMember
from msgraph.generated.models.aad_user_conversation_member import AadUserConversationMember

def load_config(config_file):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

async def create_chat(graph_client, chat_title, user_upns):
    members = [
        AadUserConversationMember(
            odata_type="#microsoft.graph.aadUserConversationMember",
            roles=["owner"],
            additional_data={
                "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{upn}')"
            }
        ) for upn in user_upns
    ]

    request_body = Chat(
        chat_type=ChatType.Group,
        topic=chat_title,
        members=members
    )

    try:
        result = await graph_client.chats.post(request_body)
        print("Chat created successfully:", result)
    except Exception as e:
        print("Error creating chat:", e)

def main():
    parser = argparse.ArgumentParser(description='Create a Microsoft Teams chat')
    parser.add_argument('--config', required=True, help='Path to the config file')
    parser.add_argument('--title', required=True, help='Title of the group chat')
    parser.add_argument('--users', required=True, help='Comma-separated list of user UPNs')
    args = parser.parse_args()

    config = load_config(args.config)

    scopes = config['graph_api']['scopes']
    tenant_id = config['azure']['tenant_id']
    client_id = config['azure']['client_id']
    client_secret=config['azure']['client_secret']

    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )

    graph_client = GraphServiceClient(credential, scopes)

    user_upns = args.users.split(',')

    asyncio.run(create_chat(graph_client, args.title, user_upns))

if __name__ == "__main__":
    main()
