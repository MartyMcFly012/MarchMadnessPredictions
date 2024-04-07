import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Fetches data from historical games and append them to existing games
def get_games(date):
    url = f"https://www.ncaa.com/march-madness-live/scores/2024/04/{date}?cid=ncaa_live_video_nav"
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

def get_games_data(start_day, end_day):
    all_games_data = []
    for i in range(start_day, end_day + 1):
        day = f"04/{i}"  # '04' needs to be changed to the correct month
        games = get_games(i)  # get_games(i) retrieves the games data for a specific day
        print("Day: " + str(i))
        
        if games is not None:
            all_games_data.append(games)
        else:
            print(f"No games today: 04/{i}")
            continue
            
    if all_games_data:
        games = pd.concat(all_games_data)
        
        # Add necessary columns and calculations
        games['Game ID'] = games.index
        games[['Field Goals Made', 'Field Goals Attempted']] = games['Field Goals'].str.split('/', expand=True).astype(int)
        games[['3 Pointers Made', '3 Pointers Attempted']] = games['3 Pointers'].str.split('/', expand=True).astype(int)
        games[['Free Throws Made', 'Free Throws Attempted']] = games['Free Throws'].str.split('/', expand=True).astype(int)
        games['FG%'] = games['Field Goals Made'] / games['Field Goals Attempted']
        numeric_cols = ['Field Goals Made', 'Field Goals Attempted', '3 Pointers Made', 
                        '3 Pointers Attempted', 'Free Throws Made', 'Free Throws Attempted', 'Score']
        games[numeric_cols] = games[numeric_cols].astype(float)
        games['FT%'] = games['Free Throws Made'] / games['Free Throws Attempted']
        games['TP%'] = games['3 Pointers Made'] / games['3 Pointers Attempted']
        row0 = games.groupby('Game ID')['Score'].transform(lambda x: x.shift(-1)).fillna(0)
        row1 = games.groupby('Game ID')['Score'].transform(lambda x: x.shift(1)).fillna(0)
        games['Off Score'] = row0 + row1
        games['Score Diff'] = games['Score'] - games['Off Score']
        games['Winner'] = games['Score Diff'].apply(lambda x: 1 if x > 0 else 0)
        games['Away or Home'] = games['Away or Home'].apply(lambda x: 0 if x == "Home team" else 1)
        games.drop(columns=['Field Goals', '3 Pointers', 'Free Throws'], inplace=True)
        games.reset_index(drop=True, inplace=True)
        games['Date'] = [f"04/{date}/2024" for date in games['Date']]
        
        # Load existing data from CSV
        try:
            og_games = pd.read_csv("updated_games.csv")
        except FileNotFoundError:
            og_games = pd.DataFrame()
        
        # Identify new games to add to the CSV
        new_games = games[~games['Game ID'].isin(og_games['Game ID'])]
        
        # Concatenate existing and new games data
        game_data = pd.concat([og_games, new_games]).reset_index(drop=True)
        
        # Save updated data to CSV
        game_data.to_csv("updated_games.csv", index=False)
    else:
        print("No new games data to process.")

# Example usage: To get data for one day, enter 'day, (day+1)'
get_games_data(6, 7)