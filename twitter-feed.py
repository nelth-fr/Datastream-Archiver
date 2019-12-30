from json import load, dump
from os import makedirs, path, getenv
from requests import get, post, codes
from logs import logger
from argparse import ArgumentParser
from dotenv import load_dotenv

""""
Defining arguments to use in command line
"""
parser = ArgumentParser(description="BOT used to Query Twitter's API")
parser.add_argument('-l', '--list', required=False, 
    help="Querying a list of defined Account.")
parser.add_argument('-t', '--tweets', dest='tweets', required=False,
    help="Querying specific Tweets tag")
parser.add_argument('-a', '--account', dest='screen_name', required=False,
    help="Querying Tweets from a specific Account")
args = parser.parse_args()

# Get API credentials from .env
load_dotenv()
CONSUMER_API_KEY = getenv('CONSUMER_API_KEY')
API_SECRET_KEY = getenv('API_SECRET_KEY')


class TwitterFeed():
    # Class Attributes
    TW_API_URL = 'https://api.twitter.com/'
    BEARER_TOKEN = ''
    TWEETS_SEARCH_ENDPOINT = '1.1/search/tweets.json?q='
    ACCOUNT_SEARCH_ENDPOINT = '1.1/statuses/user_timeline.json?screen_name='

    # Constructor
    def __init__(self):
        self.get_auth_token()

    # Class method
    def get_auth_token(self) -> None:
        body = { 
            'grant_type':'client_credentials' 
        }
        res = post(
            self.TW_API_URL + 'oauth2/token',
            auth=(CONSUMER_API_KEY, API_SECRET_KEY),
            data=body
        )
        if(res.status_code == codes.ok):
            self.BEARER_TOKEN = res.json()['access_token']
            self.args_parse_routing()
        if(res.status_code > codes.ok):
            error_message = 'Issue during connection to Twitter, verify you credentials or the URL!'
            logger.error(error_message)
            print(error_message)

    def args_parse_routing(self) -> None:
        if(args.tweets != None):
            getArgument = vars(args)['tweets']
            self.get_global_query_through_tweets(getArgument)
        if(args.list != None):
            getArgument = vars(args)['list']
            self.query_api_from_mocked_list(getArgument)
        if(args.screen_name != None):
            getArgument = vars(args)['screen_name']
            self.get_tweets_from_a_specific_user(getArgument)

    def get_tweets_from_a_specific_user(self, QUERY_PARAMETER) -> None:
        QUERY_URL = (
            self.TW_API_URL + self.ACCOUNT_SEARCH_ENDPOINT + QUERY_PARAMETER
        )
        res = get(
            QUERY_URL, headers={ 'Authorization':'Bearer ' + self.BEARER_TOKEN}
        ) 
        print('Querying Tweets from ' + QUERY_PARAMETER + "'s account.")
        self.calculate_tweets_frequency('USER', QUERY_PARAMETER, res.json())

    def query_api_from_mocked_list(self, LIST_TO_QUERY_FROM_FILE) -> None:
        with open(LIST_TO_QUERY_FROM_FILE, 'r') as inputfile:
            data = load(inputfile)
            for item in data:
                QUERY_PARAMETER = item['screen_name']
                print('Querying Tweets from: ' + QUERY_PARAMETER)
                
                QUERY_URL = (
                    self.TW_API_URL + self.ACCOUNT_SEARCH_ENDPOINT + QUERY_PARAMETER
                )
                res = get(
                    QUERY_URL, headers={ 'Authorization':'Bearer ' + self.BEARER_TOKEN }
                )
                self.calculate_tweets_frequency('USER', QUERY_PARAMETER, res.json())

    def get_global_query_through_tweets(self, QUERY_PARAMETER) -> object:
        QUERY_URL = (
            self.TW_API_URL + self.TWEETS_SEARCH_ENDPOINT + QUERY_PARAMETER,
        )
        res = get(
            QUERY_URL, headers={ 'Authorization':'Bearer ' + self.BEARER_TOKEN}
        )
        print('Querying Tweets based on ' + QUERY_PARAMETER + "'s tag.")
        self.cleaning_tweets_data('TWEETS', QUERY_PARAMETER, res.json())

    def cleaning_tweets_data(self, TYPE, QUERY_PARAMETER, API_RESULT):
        try:
            DATA = API_RESULT['statuses'] # Used to get tweets content, not metadata
            self.calculate_tweets_frequency(TYPE, QUERY_PARAMETER, DATA)
        except IndexError:
            error_message = QUERY_PARAMETER + " haven't write tweets this week !"
            logger.info(error_message)
            print(error_message + "\n")

    def calculate_tweets_frequency(self, TYPE, QUERY_PARAMETER, DATA):
        first_tweet_date = DATA[0]['created_at']
        last_tweet_date = DATA[-1]['created_at']
        print('First tweet date : ' + first_tweet_date)
        print('Last tweet date: ' + last_tweet_date + '\n')

        self.writing_in_filesystem(TYPE, QUERY_PARAMETER, DATA)

    def writing_in_filesystem(self, TYPE, QUERY_PARAMETER, DATA) -> None:
        defined_folder = './data'
        if not path.exists(defined_folder):
            makedirs(defined_folder)
        filename = f'{defined_folder}/{TYPE}' + '-' + f'{QUERY_PARAMETER}' + '.json'

        with open(filename, 'w') as file:
            dump(DATA, file)

    
if __name__ == '__main__':
    TwitterFeed()
