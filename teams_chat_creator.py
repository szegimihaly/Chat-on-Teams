#!/usr/bin/env python3

import argparse
import asyncio
import yaml
import sys
from ai_handler import AIHandler
from teams_chat import TeamsGroupChatCreator
from utils.logger import setup_logger
from colorama import Fore, Style

async def async_main(args):
    # Setup logger
    logger = setup_logger(args.debug)
    
    try:
        if args.ai_chat_only:
            if not args.ai_service:
                raise ValueError("--ai-service must be specified when using --ai-chat-only")
            
            logger.debug(f"Starting AI chat only mode with {args.ai_service}")
            with open(args.config, 'r') as config_file:
                config = yaml.safe_load(config_file)
            
            logger.debug("Initializing AI handler")
            ai_handler = AIHandler(config, args.ai_service, logger)
            logger.chat(f"\nStarting AI chat session with {args.ai_service.upper()}", color='chat_system')
            logger.chat("Commands:", color='chat_system')
            logger.chat("  /exit or /bye - End the session", color='chat_system')
            logger.chat("  /clear - Clear conversation history", color='chat_system')
            logger.chat("----------------------------------------", color='chat_system')
            
            while True:
                try:
                    user_input = input(f"{Fore.GREEN}chat> {Style.RESET_ALL}").strip()
                    if user_input.lower() in ['/exit', '/bye']:
                        logger.chat("\nEnding chat session...", color='chat_system')
                        break
                    elif user_input.lower() == '/clear':
                        ai_handler.clear_conversation()
                        logger.chat("\nConversation history cleared.", color='chat_system')
                    elif user_input:
                        logger.debug(f"Sending prompt to AI: {user_input}")
                        response, model = ai_handler.get_ai_response(user_input)
                        logger.chat(f"\n{model}: {response}\n", color='chat_ai')
                except KeyboardInterrupt:
                    logger.chat("\nEnding chat session...", color='chat_system')
                    break
                except EOFError:
                    break
        else:
            if not args.name or not args.members:
                raise ValueError("--name and --members are required when not using --ai-chat-only")
            
            logger.debug("Loading configuration file")
            with open(args.config, 'r') as config_file:
                config = yaml.safe_load(config_file)
            
            logger.debug(f"Initializing Teams chat creator with AI service: {args.ai_service}")
            ai_handler = AIHandler(config, args.ai_service, logger) if args.ai_service else None
            creator = TeamsGroupChatCreator(config, ai_handler, logger)
            
            members = [m.strip() for m in args.members.split(',')]
            logger.debug(f"Creating chat '{args.name}' with members: {members}")
            
            chat_data = await creator.create_group_chat(args.name, members)
            await creator.monitor_chat(chat_data.id, args.monitor_time)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Create MS Teams group chat and invite members')
    parser.add_argument('--config', required=True, help='Path to the configuration YAML file')
    parser.add_argument('--name', help='Name of the group chat')
    parser.add_argument('--members', help='Comma-separated list of member IDs')
    parser.add_argument('--monitor-time', type=int, default=10, help='Time in minutes to monitor the chat (default: 10)')
    parser.add_argument('--ai-service', choices=['openai', 'claude'], help='Enable AI integration with specified service')
    parser.add_argument('--ai-chat-only', action='store_true', help='Start an AI chat session without Teams integration')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()
    asyncio.run(async_main(args))

if __name__ == "__main__":
    main() 