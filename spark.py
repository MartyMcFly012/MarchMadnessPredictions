# from pyspark.sql import SparkSession
# url = "https://raw.githubusercontent.com/thomaspernet/data_csv_r/master/data/adult.csv"
# from pyspark import SparkFiles
# spark.sparkContext.addFile(url)

import requests
from bs4 import BeautifulSoup
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType


# Initialize Spark session
spark = SparkSession.builder \
    .appName("GameScores") \
    .getOrCreate()

url = "https://www.ncaa.com/march-madness-live/scores/2024/03/16?cid=ncaa_live_video_nav"  # Replace this with the actual URL of the website you want to fetch data from
response = requests.get(url)
html_content = response.text

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Find all <div> elements with class 'team-content'
divs = soup.find_all('div', class_='game-tile-data')

        
# Define schema for DataFrame
schema = StructType([
    StructField("Rank1", StringType(), True),
    StructField("Team1", StringType(), True),
    StructField("Score1", StringType(), True),
    StructField("Rank2", StringType(), True),
    StructField("Team2", StringType(), True),
    StructField("Score2", StringType(), True)
])

# Process data and create DataFrame
rows = []
for div in divs:
    data = div.get_text(separator = " ")
    lines = data.split()
    if len(lines) > 5:
        row = (lines[0], lines[1], lines[3], lines[5], lines[6], lines[8])
        rows.append(row)

# Create DataFrame
df = spark.createDataFrame(rows, schema)

# Show DataFrame
df.show()