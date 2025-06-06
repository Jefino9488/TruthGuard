from newsapi import NewsApiClient

# Init
newsapi = NewsApiClient(api_key='3947efaec8434d89ac545eb02f4b245d')
#
# # /v2/top-headlines
# top_headlines = newsapi.get_top_headlines(q='bitcoin',
#                                           sources='bbc-news,the-verge',
#                                           category='business',
#                                           language='en',
#                                           country='us')

print(newsapi.get_top_headlines(sources='bbc-news'))