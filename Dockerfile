FROM joyzoursky/python-chromedriver:3.9-selenium
WORKDIR /app
COPY scrap_headless.py /app/
COPY ./telegram_bot.py /app/
COPY ./requirements.txt /app/
COPY ./src/ /app/src/
RUN pip install -r requirements.txt