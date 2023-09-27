# LoL Webscraper

## Installation

You will need docker installed to run the headless scrapers.

For running the headful scrapers, you'll need to have the following installed:

- Python 3.9 or later
- Python packages listed in requirements.txt
- Chrome

You must make sure that in `src/scrapers/Bet365.py` the variable `chrome_path` gets updated to point to the executable
for chrome.

## Localisation

You might encounter some issues with scraping values.
This is probably due to changed names when switched to a different country.
To fix it, update the texts shown in the scraper having the issues to match the one you see when opening the website

## Running

Starting the headless webscraper with the telegram bot can be done by
running `docker-compose -f ./docker-compose-webscraper.yml up --abort-on-container-exit` in the terminal. The
path must be pointing to the folder containing the docker-compose-webscraper.yml file.

When the headful scraper should be started, you should start it locally with `python scrap_headful.py`. This requires
the installation steps done for the headful scraper, else it will fail. It doesn't start the telegram bot.

When you want to run everything, you cna use the run.sh script located at `run.sh`. It will run the headful and
headless scrapers and the telegram bot.

Outputs will be stored in the data folder.

## Telegram bot

When you want to run the telegram bot, you have to create a telegrambot. For this, message https://t.me/BotFather
with `/newbot`. Then follow the steps until you get an api token for the bot. This token should then get pasted in the
ocker-compose.yml, as the `BOT_TOKEN` environment variable.

After the bot started, message it `/register` in any chat it can view to mark the chat to receive newly added games.

Use `/unregister` to remove a chat from the new games subscribers

**NOTE**: When registering, only new games will be sent into the chat, the ones previously collected will be ignored