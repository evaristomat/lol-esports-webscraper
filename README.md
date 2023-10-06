# LoL Webscraper

## Introduction
This project provides tools to assist League of Legends enthusiasts in making informed betting decisions. We scrape odds from popular betting sites and compare them against a historical database of match outcomes.

## Features
- **Web Scraping:** 
  - Extracts betting odds for League of Legends matches from bet365, dafabet, and pinnacle.
- **Odds Comparison:** 
  - Analyzes the scraped odds.
  - Cross-references with our database of past games to highlight the best bets.
- **Past Results Analyzer:** 
  - Evaluates the success of our past best bet recommendations against newer match results.
- **Flask App:** 
  - Displays the latest best bet recommendations.
  - Facilitates user registration and login.
  - Allows users to add bets to their personal list.
  - Offers a detailed view of a user's betting history and cumulative profit.

## How to Use
1. Launch the Flask app and register.
2. Log in to access the best bet recommendations.
3. Add bets of interest to your personal list.
4. Keep track of your betting history and profit through the app's user-friendly interface.

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

