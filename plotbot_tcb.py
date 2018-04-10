import matplotlib
matplotlib.use('Agg')
import tweepy
import numpy as np
import pandas
import os
import re
from matplotlib import pyplot as plt
import seaborn as sns
import time

access_token = os.environ.get('access_token')
access_token_secret = os.environ.get('access_token_secret')
consumer_key = os.environ.get('consumer_key')
consumer_secret = os.environ.get('consumer_secret')
                    
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()

# Setup Tweepy API Authentication
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

sns.set()

checked_users_list = []
rejected_request_id_list = []
most_recent_tweet = 1

while most_recent_tweet > 0:

	for status in tweepy.Cursor(api.search, q="Analyze AND @tcbbot OR analyze AND @tcbbot", tweet_mode='extended').items(5):
		print("Starting the process - finding tweets")

		tweet = status._json

		stripped_tweet = tweet['full_text'].strip('@tcbbot ')
		split_tweet = stripped_tweet.split(' ')
		target_user = split_tweet[-1].strip('@')

		mentioner = tweet['user']['screen_name'].replace("'", "")

		try:

			if target_user not in checked_users_list:
				print("New user found")
				compound_list = []
				for status in tweepy.Cursor(api.user_timeline, id=target_user, tweet_mode='extended').items(500):
					target_user_tweet = status._json
					results = analyzer.polarity_scores(target_user_tweet["full_text"])
					compound = results["compound"]
					compound_list.append(compound)

				user_plot, comp = plt.subplots(figsize=(20, 10))

				plot_title_fonts = {'family':'sans-serif', 'size':18}

				x_axis = len(compound_list)

				comp.set_title(f"Sentiment of @{target_user}'s Past {x_axis} Tweets", fontdict=plot_title_fonts)
				comp.set_xlabel('Tweets (from oldest to newest)', fontdict=plot_title_fonts)
				comp.set_ylabel('Compound Sentiment (VADER)', fontdict=plot_title_fonts)
				comp.set_xlim(0,x_axis)
				comp.set_ylim(-1,1)

				plot_filename = f"{target_user}_sentiment_plot.png"
				plot_path = os.path.join("saved-figs", plot_filename)
				comp.plot(range(x_axis), compound_list, marker='o', color='red', mec='black', alpha=0.5)
				plt.savefig(plot_path, dpi=144)

				api.update_with_media(f"{plot_path}", f"Here is your plot of the compound sentiment for @{target_user}'s past {x_axis} tweets:")
				checked_user_list.append(target_user)
				most_recent_tweet = tweet['id']

			elif (target_user in checked_user_list) == True:
				if tweet['id'] > most_recent_tweet:
					if (tweet['id'] not in rejected_request_id_list) == True:
						api.update_status(f"{target_user}_sentiment_plot.png", 
							f"Uh oh, @{mentioner}! Someone has already plotted . Here's the plot I generated for that.")
						most_recent_tweet = tweet['id']
						rejected_request_id_list.append(tweet['id'])
						continue
					else:
						continue
				else:
					print("No new tweets")
					continue	
		except Exception as e:
			print(f"Application encountered an error: {e}")
			pass

	print("Taking a break - back in 5 minutes")
	time.sleep(300)