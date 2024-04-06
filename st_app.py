import streamlit as st
import pandas as pd
import model                        # Custom model that scales data for live inference
import st_stats                     # Simulates game outcomes
import plotly.graph_objects as go
import random
import time
from kafka import KafkaConsumer
import json
import altair as alt
# from datetime import date


st.set_page_config(
    page_title="NCAA - March Madness Predictions",
    page_icon=":basketball:",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")


@st.cache_data
def get_game_data():
	return model.games

@st.cache_data
def get_model():
	return model.model

@st.cache_data
def get_todays_games(month, day):
    return pd.read_csv(f"todays_games_{month}_{day}.csv", index_col=0)

games = get_game_data()

mm_model = get_model()


# consumer = KafkaConsumer(
#     'basketball-games',  # Topic name
#     bootstrap_servers=['kafka_broker_hostname:9092'],
#     value_deserializer=lambda m: json.loads(m.decode('utf-8'))
# )

# refreshes page when new data is available

# https://i.turner.ncaa.com/sites/default/files/images/logos/schools/bgd/{team_lower}.svg

# Would like to add logic for automating this process with safety checks (for days without games)
# month = date.today().month
# day = date.today().day
# todays_games = get_todays_games(month, day)

samples = ['03/21', '03/22', '03/23', '03/24', '03/28', '03/29', '03/30', '04/06'][::-1]

# Displays the latest retrieved games using data gathered with get_teams.py
with st.sidebar:
    example = st.selectbox("Select example date:", samples)
    
    d, m = example.split('/')

    todays_games = pd.read_csv(f"todays_games_{d}_{m}.csv", index_col=0)
    todays_games_names = pd.concat([todays_games["Away"] + " vs. " + todays_games["Home"]])

    games = games.where(games['Date'] < f"{example}/2024").dropna()
    
    st.header('Todays matches:', divider='rainbow')
    for i in range(len(todays_games)):
        team1 = todays_games.iloc[i][0]
        team2 = todays_games.iloc[i][1]
        team1_image = todays_games.iloc[i][4]
        team2_image = todays_games.iloc[i][5]
        cols = st.columns(2)
        with cols[0]:
            st.image(team1_image, caption=team1, width=50)
            st.write("")
        with cols[1]:
            st.image(team2_image, caption=team2, width=50)
        predicted_winner = model.predict_winner(team1, team2)
        st.info(f"Game {i+1}: {predicted_winner.splitlines()[0]} \n{predicted_winner.splitlines()[1]}")
    
tab1, tab2 = st.tabs(["Visualize game data", "Simulate games"])

# Plots the game stats for the latest games
with tab1:
    st.header('Visualizing historical games')
    # Convert the 'Date' column to datetime format
    games['Date'] = pd.to_datetime(games['Date'], format="mixed")
    team_list = pd.concat([todays_games['Home'], todays_games['Away']]).tolist()
    selected_games = games[games['Team'].isin(team_list)]

    # Create a selectbox to choose the column to plot
    columns = ['Score', 'Field Goals Made', '3 Pointers Made', 'Free Throws Made', 'Rebounds', 'Offensive Rebounds', 'Defensive Rebounds', 'Assists', 'Steals', 'Blocks', 'Turnovers', 'Fouls']
    selected_column = st.selectbox('Select a column to plot', columns)

    # Create the figure
    fig = go.Figure()

    # Add traces for each team
    for team, group in selected_games.groupby('Team'):
        fig.add_trace(go.Scatter(x=group['Date'], y=group[selected_column], mode='lines+markers', name=team,
                                hovertemplate='<b>%{text}</b><extra></extra>',
                                text=[f"Team: {team} <br>Score: {value}" for value in group[selected_column]]))

    # Set layout properties
    fig.update_layout(
        title=f'{selected_column} over Time',
        xaxis_title='Date',
        yaxis_title=selected_column,
        xaxis=dict(
            tickformat='%m/%d/%Y',
            tickangle=45
        ),
        hovermode='x',  # Display tooltips only for points closest to the cursor
        showlegend=True,
        height=700,  # Adjust the height of the plot
        width=900  # Adjust the width of the plot
    )

    # Show the interactive plot
    st.plotly_chart(fig)

# Uses the game statistics to simulate how a live game would play out
# Future tasks would include streaming this data from real-time games and using it for running the predictions
with tab2:
    # @st.cache_data
    st.header("Simulate game outcomes")
    st.subheader("Disclaimer: this is not gambling advice.")
    st.write("These numbers are generated using probabilities from historical data.")
    selected = st.selectbox(label = "Matches", options=todays_games_names)
    
    def simulate_game(team1, team2):
        winner = model.predict_winner(team1, team2)
        st.write(f"Pre-simulation prediction: {winner}")
        
        prediction_container = st.empty()
        
        
        team1_data = games[games["Team"] == team1]
        team2_data = games[games["Team"] == team2]
        col1, col2 = st.columns(2, gap="small")
        
        with col1:
            team1_metric_container = st.empty() 
        with col2:
            team2_metric_container = st.empty() 
        team1_score = 0
        team2_score = 0
        
        summ = st.empty()
        
        possession_team = random.choice(["Team 1", "Team 2"])
        
        prediction = None
        
        for _ in range(58):
            if possession_team == "Team 1":
                possession_score, possession_team, summary = st_stats.simulate_possession(team1_data, team1, possession_team)
                team1_score += possession_score
                team1_metric_container.metric(label=team1, value=team1_score, delta=possession_score)
                team2_metric_container.metric(label=team2, value=team2_score, delta=0)
            else:
                possession_score, possession_team, summary = st_stats.simulate_possession(team2_data, team2, possession_team)
                team2_score += possession_score
                team2_metric_container.metric(label=team2, value=team2_score, delta=possession_score)
                team1_metric_container.metric(label=team1, value=team1_score, delta=0)
            
            summ.write(summary)
            if _ <= 30:
                curr_prediction = model.predict_winner(team1, team2, team1_score, team2_score)
                if prediction != curr_prediction:
                    prediction = prediction
                prediction = curr_prediction
                prediction_container.write(prediction)
            if _ > 30:
                prediction_container.success(prediction)
            # No ties!
            if _ == 50 and team1_score == team2_score:
                _ = 40
            time.sleep(2)

    # Button to start the live game simulation
    if st.button("Simulate Live Game"):
        team1 = selected.split(" vs. ")[0]
        team2 = selected.split(" vs. ")[1]
        df = pd.DataFrame(columns = [team1, team2])
        
        simulate_game(team1, team2)


# with tab3:
#     selected = st.selectbox(label = "Matches", options=todays_games_names)
#     team1 = selected.split(" vs. ")[0]
#     team2 = selected.split(" vs. ")[1]
    
#     # read in live data with kafka consumer
#     for message in consumer:
#         game_data = message.value
#         # Process the game data as needed
#         # For example, display the data in a table
#         st.write(pd.DataFrame(game_data))
        
#     def live_predictions(team1, team2):
#         model.predict_winner(team1, team2)
#         st.experimental_rerun()
    