from kafka import KafkaProducer
import json
from time import sleep
from datetime import date
import pandas as pd
import requests
from bs4 import BeautifulSoup


def get_data(date):
    url = f'https://www.ncaa.com/march-madness-live/scores{date}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    if soup is None or soup.find("No games") != None:
        return 'No games found for this date. returning most recent games'
    games = []
    for tile in soup.select('div.team-content.svp-team-broad'):
        team_names = [team.text for team in tile.select('header.header.h7.color_lvl_-5.lvp') if not team.text.isdigit()]
        scores = [team.text for team in tile.select('header.header.h7.color_lvl_-5.lvp') if team.text.isdigit()]
        images = [img['src'] for img in tile.select('img')]
        data = {}
        if team_names != []:
            data['Away'], data['Home'] = team_names[:2]
        if len(scores) != 0:
            data['away score'], data['home score'] = scores[:2]
        else:
            data['away score'], data['home score'] = [0,0]
        if images != []:
            data['image1'], data['image2'] = images[:2]
        games.append(data)
    df = pd.DataFrame(games)
    month = date.split("/")[2]
    day = date.split("/")[3]
    df.to_csv(f"previous_games/todays_games_{month}_{day}.csv")
    return df

month = date.today().month
day = date.today().day
year = date.today().year

date_str = f"/{year}/{month}/{day}"

get_data('/2024/04/08')

# producer = KafkaProducer(bootstrap_servers=['kafka_broker_hostname:9092'],
#                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

# topic_name = 'basketball-games'

# while True:
#     game_data = get_data(date_str)
#     producer.send(topic_name, value=game_data)
#     print(f"Published game data to Kafka topic: {topic_name}")
#     sleep(120)  # Wait for 2 minutes (120 seconds)

# producer.flush()
# producer.close()