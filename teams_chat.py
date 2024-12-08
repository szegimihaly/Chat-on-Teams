from datetime import datetime
import time
import asyncio
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.chat import Chat
from msgraph.generated.models.chat_type import ChatType
from msgraph.generated.models.aad_user_conversation_member import AadUserConversationMember

class TeamsGroupChatCreator:
    def __init__(self, config, ai_handler=None, logger=None):
        self.config = config
        self.logger = logger
        
        self.logger.debug("Initializing Teams chat creator")
        self.credential = ClientSecretCredential(
            tenant_id=self.config['azure']['tenant_id'],
            client_id=self.config['azure']['client_id'],
            client_secret=self.config['azure']['client_secret']
        )
        
        self.logger.debug("Creating Graph client")
        self.graph_client = GraphServiceClient(
            self.credential,
            self.config['graph_api']['scopes']
        )
        
        self.ai_handler = ai_handler
        self.chat_id = None

    async def create_group_chat(self, chat_name, members):
        self.logger.debug(f"Creating chat members list with owner: {self.config['azure']['owner_id']}")
        chat_members = [
            AadUserConversationMember(
                odata_type="#microsoft.graph.aadUserConversationMember",
                roles=["owner"],
                additional_data={
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{self.config['azure']['owner_id']}')"
                }
            )
        ]

        for member in members:
            self.logger.debug(f"Adding member to chat: {member}")
            chat_members.append(
                AadUserConversationMember(
                    odata_type="#microsoft.graph.aadUserConversationMember",
                    roles=[],
                    additional_data={
                        "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{member}')"
                    }
                )
            )

        request_body = Chat(
            chat_type=ChatType.Group,
            topic=chat_name,
            members=chat_members
        )

        try:
            self.logger.debug("Sending chat creation request")
            result = await self.graph_client.chats.post(request_body)
            self.logger.info(f"Successfully created group chat: {result.id}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to create chat: {str(e)}")
            raise Exception(f"Failed to create chat: {str(e)}")

    async def send_chat_message(self, message_content):
        if not self.chat_id:
            raise Exception("Chat ID not set")
            
        try:
            await self.graph_client.chats.by_chat_id(self.chat_id).messages.post(content=message_content)
        except Exception as e:
            raise Exception(f"Failed to send message: {str(e)}")

    async def monitor_chat(self, chat_id, duration_minutes=10):
        self.chat_id = chat_id
        end_time = time.time() + (duration_minutes * 60)
        last_message_id = None
        
        self.logger.chat(f"\nMonitoring chat for {duration_minutes} minutes...")
        self.logger.chat("----------------------------------------")
        if self.ai_handler:
            self.logger.chat("AI Integration enabled - Use '!hi AI!' to interact with the AI")

        while time.time() < end_time:
            try:
                messages = await self.graph_client.chats.by_chat_id(chat_id).messages.get()
                
                for message in reversed(messages.value):
                    if message.id != last_message_id:
                        created_time = datetime.fromisoformat(message.created_date_time.replace('Z', '+00:00'))
                        from_user = message.from_user.display_name if message.from_user else 'Unknown'
                        content = message.content
                        
                        self.logger.chat(f"\n[{created_time.strftime('%Y-%m-%d %H:%M:%S')}] {from_user}:", color='chat_timestamp')
                        self.logger.chat(f"{content}", color='chat_user')
                        
                        if self.ai_handler and content.startswith('!hi AI!'):
                            prompt = content[8:].strip()
                            if prompt:
                                self.logger.chat("\nProcessing AI request...", color='chat_system')
                                response, model = self.ai_handler.get_ai_response(prompt)
                                await self.send_chat_message(f"{model}: {response}")
                        
                        last_message_id = message.id
                
                members = await self.graph_client.chats.by_chat_id(chat_id).members.get()
                for member in members.value:
                    display_name = member.display_name or 'Unknown'
                    roles = member.roles or []
                    role_str = ' (Owner)' if 'owner' in roles else ''
                    self.logger.chat(f"\nMember: {display_name}{role_str}")

            except Exception as e:
                self.logger.error(f"Error while monitoring chat: {str(e)}")
            
            await asyncio.sleep(5) 