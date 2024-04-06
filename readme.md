This was a project to see if I could use real-time March Madness data to predict the winners of match-ups. I used web scraping to gather data from the NCAA website and then trained a RandomForestRegressor model on the features that were most indicative of a win (using a correlation matrix to identify which variables had the strongest correlations with Score). Then based on the predicted score, a winner would be determined.

To run this project locally:
Git clone the repository to your local machine.
Open terminal and navigate to the cloned folder.
Run streamlit run st_app.py
