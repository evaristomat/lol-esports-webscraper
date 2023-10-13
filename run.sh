#!/bin/bash

# Start telegram service
docker-compose -f ./docker-compose-telegram.yml up -d

# Run the scraping script
python ./scrap_headful.py

# Start webscraper service and abort if any container exits
docker-compose -f ./docker-compose-webscraper.yml up --abort-on-container-exit

# Run update db
python ./database/update.py

# Run update db transformed
python ./database/data_transformation.py

# Run best bets
python ./stats/get_best_bets.py

# Run results
python ./bets/get_results.py

# Send telegram bets
python ./telegram_bot/test.py