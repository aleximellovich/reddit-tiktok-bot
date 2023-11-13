#!/usr/bin/python
import random
from bot_functions import get_content, get_audio, authenticate_reddit, print_content

subreddit_list = ["askreddit", 'maliciouscompliance', 'tifi', 'pettyrevenge', 'prorevenge']
subreddit = random.choice(subreddit_list)
reddit = authenticate_reddit()

content = get_content(subreddit,  reddit)
get_audio(content["body"])

print_content(content)