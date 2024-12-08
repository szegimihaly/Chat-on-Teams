import openai
from anthropic import Anthropic

class AIHandler:
    def __init__(self, config, service_type, logger):
        self.service_type = service_type
        self.config = config.get('ai_services', {})
        self.logger = logger
        self.conversation_history = []
        
        self.logger.debug(f"Initializing {service_type} handler")
        if service_type == 'openai':
            openai.api_key = self.config['openai']['api_key']
            self.model = self.config['openai']['model']
            self.logger.debug(f"Using OpenAI model: {self.model}")
            # Initialize with system message
            self.conversation_history = [
                {"role": "system", "content": "You are a helpful assistant in a chat conversation."}
            ]
        elif service_type == 'claude':
            self.anthropic = Anthropic(api_key=self.config['anthropic']['api_key'])
            self.model = self.config['anthropic']['model']
            self.logger.debug(f"Using Claude model: {self.model}")
            # Initialize with system message
            self.conversation_history = [
                {"role": "system", "content": "You are a helpful assistant in a chat conversation."}
            ]
    
    def get_ai_response(self, prompt):
        try:
            self.logger.debug(f"Sending request to {self.service_type}")
            
            if self.service_type == 'openai':
                # Add user message to history
                self.conversation_history.append({"role": "user", "content": prompt})
                
                response = openai.chat.completions.create(
                    model=self.config['openai']['model'],
                    messages=self.conversation_history,
                    max_tokens=self.config['openai']['max_tokens'],
                    temperature=self.config['openai']['temperature']
                )
                
                # Add assistant's response to history
                assistant_message = response.choices[0].message.content
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                
                self.logger.debug("Received response from OpenAI")
                return assistant_message, self.model
                
            elif self.service_type == 'claude':
                # Add user message to history
                self.conversation_history.append({"role": "user", "content": prompt})
                
                response = self.anthropic.messages.create(
                    model=self.config['anthropic']['model'],
                    max_tokens=self.config['anthropic']['max_tokens'],
                    temperature=self.config['anthropic']['temperature'],
                    messages=self.conversation_history
                )
                
                # Add assistant's response to history
                assistant_message = response.content[0].text
                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                
                self.logger.debug("Received response from Claude")
                return assistant_message, self.model
                
        except Exception as e:
            self.logger.error(f"Error in AI response: {str(e)}")
            return f"Error getting AI response: {str(e)}", "ERROR"
    
    def clear_conversation(self):
        """Reset the conversation history"""
        if self.service_type == 'openai':
            self.conversation_history = [
                {"role": "system", "content": "You are a helpful assistant in a chat conversation."}
            ]
        elif self.service_type == 'claude':
            self.conversation_history = [
                {"role": "system", "content": "You are a helpful assistant in a chat conversation."}
            ]
        self.logger.debug("Conversation history cleared")