# Japanese and English Grammar Check Discord Bot

This project implements a bot that checks Japanese and English grammar within a Discord server. When a user sends a message containing `:pls_ck:`,  
the bot analyzes the text and provides feedback as needed.

## Main Features

- Japanese and English grammar checking
- Identification of unnatural expressions and suggestion of corrections
- Provision of detailed explanations

## Technology Stack

- Python 3.11
- Discord.py
- OpenAI API (GPT-4 model)
- Pydantic

## Setup Instructions

1. Clone this repository.
2. Rename the `env.example` file to `.env` and set the necessary environment variables.
   - `OPENAI_API_KEY`: OpenAI API key
   - `DISCORD_BOT_TOKEN`: Discord bot token ID
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Start the bot:
   ```
   python main.py
   ```

## Usage

1. Invite the bot to your Discord server.
2. Send a message containing `:pls_ck:`.
3. The bot will check the grammar and provide feedback as needed.

## Notes

- The `.env` file containing environment variables is added to `.gitignore` and will not be pushed to public repositories.
- This bot can also be containerized using Docker.

## License

This project is released under the MIT License. For details, please refer to the `LICENSE` file.
