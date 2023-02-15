# grabber_tg
## About
This bot collects posts from public channels over a specified period of time (typically one to three hours ago, with the first hour skipped so that reactions can accumulate). It then checks that the posts were not forwarded, to avoid duplicates. The posts are sorted by the number of reactions relative to the channel's subscriber count, and the specified number of posts are taken. Finally, these posts are sent to a Telegram channel at random intervals within the set time.

## Installation
1. clone
2. install virtual environment
3. install dependencies from requirmenets.txt
4. Create and populate the .env, like .example.env (you can get API_ID, API_HASH here - https://my.telegram.org/)
5. Set your preferences to run.py
6. Run run.py