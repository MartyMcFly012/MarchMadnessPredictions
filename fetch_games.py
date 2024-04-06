import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Fetches data from historical games
def get_games(date):
    url = f"https://www.ncaa.com/march-madness-live/scores/2024/03/{date}?cid=ncaa_live_video_nav"
    response = requests.get(url)
    html_content = response.text

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all tile wrappers
    tile_wrappers = soup.select('div.tile-wrapper')
    if tile_wrappers == []:
        return None
    
    visited = []

    # Loop through each tile wrapper
    for tile_wrapper in tile_wrappers:
        # Get the tile link
        tile_link = tile_wrapper.select_one('a.tile-link')
        if tile_link:
            tile_link = tile_link.get('href')
        else:
            tile_link = None
        
        if tile_link not in visited:
            visited.append(tile_link)

    # Create an empty list to hold the DataFrame for each game
    game_dfs = []

    # Loop through each game and fetch the data
    for game in visited:
        game_data = get_data(game, date)
        if game_data is not None:
            game_dfs.append(game_data)

    # Combine all DataFrames into a single DataFrame
    return pd.concat(game_dfs)

def get_data(game_id, date):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless=new')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    url2 = f"https://www.ncaa.com{game_id}"
    driver.get(url2)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    team_stats_div = soup.find("div", class_="team-stats")
    scores = [score.get_text() for score in soup.find_all("h1", class_="mml-h1")]
    ranks = [score.get_text() for score in soup.find_all("span", class_="overline color_lvl_-5 svp mvp")]
    if team_stats_div:
        team_names = [span.get_text() for span in team_stats_div.select(".statHeaderValA .overline, .statHeaderValH .overline")]
        stat_names = [p.get_text() for p in team_stats_div.select(".statName .caption")]
        team_stats = [body.get_text() for body in team_stats_div.select(".statValA .body")]
        opponent_stats = [body.get_text() for body in team_stats_div.select(".statValH .body")]
        data = {}
        
        data["Team"] = team_names
        data['Away or Home'] = ["Away team", "Home team"]
        data["Score"] = scores
        data["Rank"] = ranks
        data["Date"] = date
        
        for i, stat_name in enumerate(stat_names):
            data[stat_name] = [team_stats[i], opponent_stats[i]]
            
        df = pd.DataFrame(data)
        df = df.T
        df.columns = [game_id.split("/")[-1],game_id.split("/")[-1]]
        df = df.T
        return df

# Uncomment to run the script for several days
all_games_data = []
for i in range(30, 32):
    day = f"03/{i}" # change for correct month
    games = get_games(i)
    print("day: " + str(i))
    if games is not None:
        all_games_data.append(games)
    else:
        print("No games today: 03/" + str(i))
        continue
games = pd.concat(all_games_data)

# To runt the data for a specific day and add it to the overall data
# games = get_games(29)

games['Game ID'] = games.index

games[['Field Goals Made', 'Field Goals Attempted']] = games['Field Goals'].str.split('/', expand=True).astype(int)
games[['3 Pointers Made', '3 Pointers Attempted']] = games['3 Pointers'].str.split('/', expand=True).astype(int)
games[['Free Throws Made', 'Free Throws Attempted']] = games['Free Throws'].str.split('/', expand=True).astype(int)
games["FG%"] = games['Field Goals Made'] / games['Field Goals Attempted']

# Convert the components to float
numeric_cols = ['Field Goals Made', 'Field Goals Attempted', 
                '3 Pointers Made', '3 Pointers Attempted', 
                'Free Throws Made', 'Free Throws Attempted', "Score"]
games[numeric_cols] = games[numeric_cols].astype(float)
# Calculate the total score for each team
games["FG%"] = games['Field Goals Made'] / games['Field Goals Attempted']
games["FT%"] = games['Free Throws Made'] / games['Free Throws Attempted']
games["TP%"] = games['3 Pointers Made'] / games['3 Pointers Attempted']

# Add Off Score
row0 = games.groupby('Game ID')['Score'].transform(lambda x: x.shift(-1)).fillna(0)
row1 = games.groupby('Game ID')['Score'].transform(lambda x: x.shift(1)).fillna(0)
games["Off Score"] = row0+row1

# Calculate the score difference for each game
games['Score Diff'] = (games["Score"] - games["Off Score"])
games['Winner'] = games['Score Diff'].apply(lambda x: 1 if x > 0 else 0)
games['Away or Home'] = games['Away or Home'].apply(lambda x: 0 if x == "Home team" else 1)
games.ffill(inplace=True)
games.ffill(inplace=True)
games.drop(columns=['Field Goals','3 Pointers', 'Free Throws'], inplace=True)
games.reset_index(drop=True, inplace=True)

# Will need to change to match month
games["Date"] = [f"03/{date}/2024" for date in games["Date"]]

og_games = pd.read_csv("games.csv")

game_data = pd.concat([og_games, games]).reset_index(drop=True).drop(columns="Unnamed: 0")
game_data.to_csv("updated_games.csv", index=False)
