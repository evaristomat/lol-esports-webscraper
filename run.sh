#!/bin/bash

docker-compose -f ./docker-compose-telegram.yml up -d
python ./scrap_headful.py
docker-compose -f ./docker-compose-webscraper.yml up --abort-on-container-exit