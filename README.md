This is a compilation of some barebone code for a discord bot. These directions are written to run inside of a linux terminal. 

Installing python/pip:

`sudo apt install python3 python3-pip`

To install the required packages, navigate to the directory where `requirements.txt` and your other bot files are located, and run: 

`pip install -r requirements.txt`

The `.env` file is short for "environment" and is used to store secret variables or config settings in a dedicated space, so that the rest of the code that the bot runs on can be shared through e.g. GitHub without exposing sensitive information like the bot's token. For this demo, the only thing stored in .env is `DISCORD_TOKEN` which is used as the login credentials and to perform actions on the bot account.