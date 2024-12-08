# Teams Chat Creator

A command-line application that creates Microsoft Teams group chats, invites members, monitors chat activity, and optionally integrates with AI services (OpenAI GPT or Anthropic Claude) for interactive responses. The application can be used via command line or through a modern web interface.

- [Teams Chat Creator](#teams-chat-creator)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
    - [Setting up Python Virtual Environment](#setting-up-python-virtual-environment)
  - [Configuration](#configuration)
  - [Usage](#usage)
    - [Running the Web Interface](#running-the-web-interface)
    - [AI-Only Mode](#ai-only-mode)
    - [Basic Usage (Without AI)](#basic-usage-without-ai)
    - [AI Integration](#ai-integration)
    - [Custom Monitoring Duration](#custom-monitoring-duration)
  - [Web Interface Features](#web-interface-features)
  - [Command Line Arguments](#command-line-arguments)
  - [AI Integration Features](#ai-integration-features)
  - [Output Format](#output-format)
  - [Error Handling](#error-handling)
  - [Security Notes](#security-notes)
  - [License](#license)

## Features

- Create Microsoft Teams group chats
- Invite multiple members to the chat
- Monitor chat activity in real-time
- Display chat messages with timestamps
- Show member status and roles
- Modern web interface with dark mode support
- AI integration (optional)
  - Support for OpenAI GPT models
  - Support for Anthropic Claude models
  - Interactive AI responses triggered by chat messages
  - AI-only mode for direct AI interactions

## Prerequisites

- Python 3.7 or higher
- Azure AD application with the following permissions:
  - Chat.Create
  - Chat.ReadWrite.All
  - Chat.Read.All
- For AI integration:
  - OpenAI API key (for GPT integration)
  - Anthropic API key (for Claude integration)

## Installation

### Setting up Python Virtual Environment

1. Create a new virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

2. Clone the repository or download the source code
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `config.yaml` file with your credentials and settings:

```yaml
azure:
  tenant_id: "your-tenant-id"
  client_id: "your-client-id"
  client_secret: "your-client-secret"
  owner_id: "default-owner-user-id"  # This will be the user who creates/owns the chat
graph_api:
  base_url: "https://graph.microsoft.com/v1.0"
  scopes:
    - "https://graph.microsoft.com/.default"
ai_services:
  openai:
    api_key: "your-openai-api-key"
    model: "gpt-4"  # or gpt-3.5-turbo
    max_tokens: 1000
    temperature: 0.7
  anthropic:
    api_key: "your-anthropic-api-key"
    model: "claude-3-sonnet-20240229"  # or other Claude model
    max_tokens: 1000
    temperature: 0.7
```

## Usage

### Running the Web Interface

1. Start the web server:

```bash
python web_app.py
```

2. Open your web browser and navigate to:

```text
http://localhost:8000
```

The web interface provides:

- Real-time chat monitoring
- Easy AI service connection
- Dark/Light mode toggle
- Debug mode for troubleshooting
- Responsive design for all screen sizes

### AI-Only Mode

You can use the application in AI-only mode to interact directly with AI services without Teams integration:

```bash
python teams_chat_creator.py --config config.yaml --ai-only --ai-service openai
```

Or through the web interface:

1. Open the web UI
2. Click either "Connect OpenAI" or "Connect Claude"
3. Start chatting directly with the AI

Features in AI-only mode:

- Direct AI interactions without Teams
- Switch between AI services
- Full chat history
- Debug logging
- All AI capabilities without Microsoft Teams requirements

### Basic Usage (Without AI)

Create a group chat and monitor it for 10 minutes:

```bash
python teams_chat_creator.py --config config.yaml --name "Project Discussion" --members "user1@example.com,user2@example.com" --monitor-time 10
```

### AI Integration

Enable AI integration with OpenAI:

```bash
python teams_chat_creator.py --config config.yaml --name "AI-Enabled Chat" --members "user1@example.com,user2@example.com" --monitor-time 10 --ai-service openai
```

Enable AI integration with Anthropic:

```bash
python teams_chat_creator.py --config config.yaml --name "Claude Chat" --members "user1@example.com,user2@example.com" --monitor-time 10 --ai-service anthropic
```

### Custom Monitoring Duration

Monitor the chat for a specific duration (e.g., 30 minutes):

```bash
python teams_chat_creator.py --config config.yaml --name "Custom Duration Chat" --members "user1@example.com,user2@example.com" --monitor-time 30 --ai-service openai
```

## Web Interface Features

The web interface provides several features for easy interaction:

1. Connection Management:
   - Connect to OpenAI or Claude with one click
   - Visual indicators for active connections
   - Easy service switching

2. Chat Interface:
   - Clean, modern design
   - Message history with clear sender identification
   - Easy-to-use input field
   - Send button and Enter key support

3. Debug Features:
   - Toggle debug mode for detailed logs
   - Real-time connection status
   - Message delivery confirmation
   - Service state monitoring

4. Theme Support:
   - Dark mode for reduced eye strain
   - Light mode for high contrast
   - Persistent theme selection

5. Responsive Design:
   - Works on desktop and mobile devices
   - Adaptive layout for different screen sizes
   - Touch-friendly interface

## Command Line Arguments

- `--config`: Path to the configuration YAML file (required)
- `--name`: Name of the group chat (required)
- `--members`: Comma-separated list of member IDs/emails (required)
- `--monitor-time`: Time in minutes to monitor the chat (default: 10)
- `--ai-service`: AI service to use (optional, choices: 'openai' or 'claude')

## AI Integration Features

When AI integration is enabled, chat participants can interact with the AI by starting their message with `!hi AI!`. For example:

`!hi AI! What is the capital of France?`

The AI will respond in the chat with the answer.

## Output Format

The application displays:

- Chat creation confirmation
- Real-time messages with timestamps and sender information
- Member status updates
- AI responses (when enabled)

Example output:

```bash
Successfully created group chat: 19:meeting_MjdhN...
Monitoring chat for 10 minutes...
----------------------------------------
AI Integration enabled - Use '!hi AI!' to interact with the AI
Member: John Doe (Owner)
Member: Jane Smith
[2024-01-20 14:30:15] John Doe:
Hello everyone!
[2024-01-20 14:30:45] Jane Smith:
!hi AI! What's the weather like in Paris?
[2024-01-20 14:30:47] Teams Chat Bot:
AI Response:
I apologize, but I don't have access to real-time weather data. To get accurate weather information for Paris, I recommend checking a weather service or website.
----------------------------------------
```

## Error Handling

The application includes comprehensive error handling for:

- Configuration issues
- Authentication failures
- API errors
- AI service integration problems

Errors are displayed on stderr with descriptive messages.

## Security Notes

- Keep your `config.yaml` file secure and never commit it to version control
- Store API keys and credentials securely
- Use environment variables for sensitive information in production

## License

This project is licensed under the AGPL v3 License. See the LICENSE file for details.
