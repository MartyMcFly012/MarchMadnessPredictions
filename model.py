import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

games = pd.read_csv('updated_games.csv', index_col=0)

# Split the 'Field Goals', '3 Pointers', and 'Free Throws' columns
features = ['Score', 'Field Goals Made', 'Field Goals Attempted', 'FG%', 'Assists', 'Free Throws Made', 'TP%']
# features = ['Team', 'Score', 'FT%', 'FG%', 'TP%']

# X = all_games.drop(columns = 'Team')
# y = all_games['Score']
X = games[features]
y = games['Score']

# Split the data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor()

model.fit(X_train, y_train)
# Function to predict the winner between two teams

def scale_data(data, means, stds):
    scaled_data = {}
    for feature, value in data.items():
        if feature in stds.index:  # Check if feature exists in precomputed values
            scaled_data[feature] = (value - means[feature]) / (stds[feature] + 1)
        else:
            scaled_data[feature] = value  # Keep unscalable features untouched
    return scaled_data

def predict_winner(team1, team2, score1=0, score2=0):
    teams = [team1, team2]
    # placeholder_values1 = {}
    # placeholder_values2 = {}
    # placeholder_values = [placeholder_values1, placeholder_values2]

    # for team, pv in zip(teams, placeholder_values):
    #     stats = games[games["Team"] == team]
    #     if len(stats) > 1:
    #         feature_means = stats[features].mean()
    #         feature_std = stats[features].std()
    #     else:
    #         continue
    #     for feature in features:
    #         # Scale the features based on mean and standard deviation
    #         pv[feature] = (np.random.normal(feature_means[feature], feature_std[feature]) - feature_means[feature]) / (feature_std[feature] + 1)
    
    # if score1 != 0:
    #     placeholder_values[0]['Score'] = score1
    # if score2 != 0:
    #     placeholder_values[1]['Score'] = score2
    # team1_stats = games[games["Team"] == team1][features]
    # team2_stats = games[games["Team"] == team2][features]
    
    # team1_means = team1_stats.mean()
    # team1_stds = team1_stats.std()
    # team2_means = team2_stats.mean()
    # team2_stds = team2_stats.std()

    # # Scale the placeholder values
    # placeholder_values[0] = scale_data(placeholder_values[0], team1_means, team1_stds)
    # placeholder_values[1] = scale_data(placeholder_values[1], team2_means, team2_stds)

    # team1_data = pd.DataFrame(placeholder_values1, columns=features, index=[0])
    # team2_data = pd.DataFrame(placeholder_values2, columns=features, index=[0])
    team1_mean = games[games["Team"] == team1]['Score'].mean()
    team2_mean = games[games["Team"] == team2]['Score'].mean() 
    
    if score1 == 0:
        team1_score = team1_mean
    else:
        team1_score = score1 * (team1_mean / (score1 + 1))
    if score2 == 0:
        team2_score = team2_mean
    else:
        team2_score = score2 * (team2_mean / (score2 + 1))
    
    team1_data = games[games["Team"] == team1][features]
    team2_data = games[games["Team"] == team2][features]
    
    team1_data['Score'] = team1_score
    team2_data['Score'] = team2_score
    
    team1_pred = model.predict(team1_data)[0].round()
    team2_pred = model.predict(team2_data)[0].round()
    
    # score_diff = score1 - score2
    
    # if score_diff > 0:
    #     team1_pred += score_diff
    # else:
    #     team2_pred += (score_diff * -1)
    
    if team1_pred > team2_pred:
        return f"{team1} is predicted to win with {team1_pred} points. \n Final score: {team1} {team1_pred} - {team2} {team2_pred}"
    else:
        return f"{team2} is predicted to win with {team2_pred} points. \n Final score: {team2} {team2_pred} - {team1} {team1_pred}"
    
predict_winner("NC State", "Duke")