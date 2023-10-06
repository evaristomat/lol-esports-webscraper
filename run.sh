#!/bin/bash

# Start telegram service
docker-compose -f ./docker-compose-telegram.yml up -d

# Run the scraping script
python ./scrap_headful.py

# Start webscraper service and abort if any container exits
docker-compose -f ./docker-compose-webscraper.yml up --abort-on-container-exit

# Run the update_dafa_dragons.py to replace the JSON keys
python ./update_dafa_dragons.py

# Run best bets
python ./stats/get_best_bets.py

# Run results
python ./bets/get_results.py