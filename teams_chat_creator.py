#!/usr/bin/env python3

import argparse
import yaml
import sys
import time
from datetime import datetime
from msgraph.core import GraphClient
from azure.identity import ClientSecretCredential
import openai
from anthropic import Anthropic

class AIHandler:
    def __init__(self, config, service_type):
        self.service_type = service_type
        self.config = config.get('ai_services', {})
        
        if service_type == 'openai':
            openai.api_key = self.config['openai']['api_key']
        elif service_type == 'claude':
            self.anthropic = Anthropic(api_key=self.config['anthropic']['api_key'])
    
    def get_ai_response(self, prompt):
        try:
            if self.service_type == 'openai':
                response = openai.ChatCompletion.create(
                    model=self.config['openai']['model'],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.config['openai']['max_tokens'],
                    temperature=self.config['openai']['temperature']
                )
                return response.choices[0].message.content
                
            elif self.service_type == 'claude':
                response = self.anthropic.messages.create(
                    model=self.config['anthropic']['model'],
                    max_tokens=self.config['anthropic']['max_tokens'],
                    temperature=self.config['anthropic']['temperature'],
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
        except Exception as e:
            return f"Error getting AI response: {str(e)}"

class TeamsGroupChatCreator:
    def __init__(self, config_path, ai_service=None):
        with open(config_path, 'r') as config_file:
            self.config = yaml.safe_load(config_file)
        
        self.credential = ClientSecretCredential(
            tenant_id=self.config['azure']['tenant_id'],
            client_id=self.config['azure']['client_id'],
            client_secret=self.config['azure']['client_secret']
        )
        self.graph_client = GraphClient(credential=self.credential)
        
        # Initialize AI handler if service is specified
        self.ai_handler = AIHandler(self.config, ai_service) if ai_service else None
        self.chat_id = None

    def create_group_chat(self, chat_name, members):
        # Prepare the chat creation request
        chat_request = {
            "chatType": "group",
            "topic": chat_name,
            "members": [
                {
                    "@odata.type": "#microsoft.graph.aadUserConversationMember",
                    "roles": ["owner"],
                    "user@odata.bind": f"https://graph.microsoft.com/v1.0/users/{self.config['azure']['owner_id']}"
                }
            ]
        }

        # Add members to the request
        for member in members:
            chat_request["members"].append({
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": [],
                "user@odata.bind": f"https://graph.microsoft.com/v1.0/users/{member}"
            })

        # Create the chat
        response = self.graph_client.post(
            "/v1.0/chats",
            json=chat_request
        )
        
        if response.status_code == 201:
            chat_data = response.json()
            print(f"Successfully created group chat: {chat_data['id']}")
            return chat_data
        else:
            raise Exception(f"Failed to create chat: {response.text}")

    def send_chat_message(self, message_content):
        if not self.chat_id:
            raise Exception("Chat ID not set")
            
        message_request = {
            "body": {
                "content": message_content
            }
        }
        
        response = self.graph_client.post(
            f"/v1.0/chats/{self.chat_id}/messages",
            json=message_request
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to send message: {response.text}")

    def monitor_chat(self, chat_id, duration_minutes=10):
        self.chat_id = chat_id
        end_time = time.time() + (duration_minutes * 60)
        last_message_id = None
        
        print(f"\nMonitoring chat for {duration_minutes} minutes...")
        print("----------------------------------------")
        if self.ai_handler:
            print("AI Integration enabled - Use '!hi AI!' to interact with the AI")

        while time.time() < end_time:
            try:
                # Get chat messages
                response = self.graph_client.get(
                    f"/v1.0/chats/{chat_id}/messages?$top=50&$orderby=createdDateTime desc"
                )
                
                if response.status_code == 200:
                    messages = response.json().get('value', [])
                    
                    for message in reversed(messages):
                        if message['id'] != last_message_id:
                            created_time = datetime.fromisoformat(message['createdDateTime'].replace('Z', '+00:00'))
                            from_user = message.get('from', {}).get('user', {}).get('displayName', 'Unknown')
                            content = message.get('body', {}).get('content', '')
                            
                            print(f"\n[{created_time.strftime('%Y-%m-%d %H:%M:%S')}] {from_user}:")
                            print(f"{content}")
                            
                            # Handle AI interaction
                            if self.ai_handler and content.startswith('!hi AI!'):
                                prompt = content[8:].strip()  # Remove '!hi AI!' prefix
                                if prompt:
                                    print("\nProcessing AI request...")
                                    ai_response = self.ai_handler.get_ai_response(prompt)
                                    self.send_chat_message(f"AI Response:\n{ai_response}")
                            
                            last_message_id = message['id']
                
                # Get chat members status
                members_response = self.graph_client.get(
                    f"/v1.0/chats/{chat_id}/members"
                )
                
                if members_response.status_code == 200:
                    members = members_response.json().get('value', [])
                    for member in members:
                        display_name = member.get('displayName', 'Unknown')
                        roles = member.get('roles', [])
                        role_str = ' (Owner)' if 'owner' in roles else ''
                        print(f"\nMember: {display_name}{role_str}")

            except Exception as e:
                print(f"Error while monitoring chat: {str(e)}", file=sys.stderr)
            
            time.sleep(5)

def main():
    parser = argparse.ArgumentParser(description='Create MS Teams group chat and invite members')
    parser.add_argument('--config', required=True, help='Path to the configuration YAML file')
    parser.add_argument('--name', required=True, help='Name of the group chat')
    parser.add_argument('--members', required=True, help='Comma-separated list of member IDs')
    parser.add_argument('--monitor-time', type=int, default=10, help='Time in minutes to monitor the chat (default: 10)')
    parser.add_argument('--ai-service', choices=['openai', 'claude'], help='Enable AI integration with specified service')

    args = parser.parse_args()
    
    try:
        creator = TeamsGroupChatCreator(args.config, args.ai_service)
        members = [m.strip() for m in args.members.split(',')]
        
        chat_data = creator.create_group_chat(args.name, members)
        creator.monitor_chat(chat_data['id'], args.monitor_time)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    print("\nChat monitoring completed.")

if __name__ == "__main__":
    main() 