import random
import pandas as pd

pd.options.mode.chained_assignment = None

def simulate_possession(team_stats, team, possession_team):
    score = 0
    summary = []  # Initialize an empty list to store the checks

    # Field Goal Attempt
    if random.random() < team_stats['FG%'].mean():
        score += 2
        summary.append(f"{team} scored a field goal (2 points)")
    elif random.random() < team_stats['TP%'].mean():
        score += 3
        summary.append(f"{team} scored a three-pointer (3 points)")

    # Check for shooting fouls
    if score > 0:
        if random.random() < team_stats['Fouls'].mean():
            # Shooting foul
            if score == 2:
                if random.random() < team_stats['FT%'].mean():
                    score += 1
                    summary.append(f"{team} scored a free throw (1 point)")
                if random.random() < team_stats['FT%'].mean():
                    score += 1
                    summary.append(f"{team} scored a free throw (1 point)")

    # Check for rebounds
    if score == 0:
        if random.random() < team_stats['Offensive Rebounds'].mean() / team_stats['Rebounds'].mean():
            # Offensive rebound, continue possession
            summary.append(f"{team} got an offensive rebound")
        else:
            # Defensive rebound, end possession and switch to other team
            if possession_team == "Team 1":
                possession_team = "Team 2"
                summary.append(f"{team} got a defensive rebound")
            else:
                possession_team = "Team 1"
                summary.append(f"{team} got a defensive rebound")

    # Check for non-shooting fouls
    if (random.random() < team_stats['Fouls'].mean()) and (score == 2):  # Assuming fouls per 10 possessions
        if random.random() < team_stats['FT%'].mean():
            score += 1
            summary.append(f"{team} scored a free throw (1 point) due to a non-shooting foul")
        if random.random() < team_stats['FT%'].mean() * team_stats['FT%'].mean():
            score += 1
            summary.append(f"{team} scored a free throw (1 point) due to a non-shooting foul")

    # Check for turnovers
    if random.random() < team_stats['Turnovers'].mean():  # Assuming turnovers per 10 possessions
        # End possession and switch to other team
        if possession_team == "Team 1":
            possession_team = "Team 2"
            summary.append(f"{team} turned the ball over")
        else:
            possession_team = "Team 1"
            summary.append(f"{team} turned the ball over")

    return score, possession_team, summary