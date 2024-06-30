# Watertrust tweet counts
These files represent the first stage of data provision, with counts of tweets matching the desired keywords.

## Base dataset
The files included here contain numbers describing a base dataset which is not provided for reasons of human research ethics.

The base dataset contains a total of 314,927 tweets (including retweets).

### Dataset parameters
The dataset is an extract of tweets from the [Australian Twittersphere](https://www.digitalobservatory.net.au/resources/australian-twittersphere/).

Tweets are included from 1 November 2018 to 30 June 2023. All date thresholds are calculated in Sydney time.

Tweets are included which contain one or more of the following keywords in their text (regular expression matching is used, case insensitive):

- basin ?plan
- basin ?authority
- mdba
- mdbp
- river ?murray
- murray ?river
- river ?murray
- river ?darling
- murray[ -]?darling


### Data notes

The number of Twitter accounts in the Australian Twittersphere was increased at several points when the Australian Twittersphere population was refreshed - see the [fact sheet](https://qut-digital-observatory.github.io/australian_twittersphere_fact_sheet/) for more information. This influences the number of tweets over time, and will affect any comparisons of the number of matching tweets at different time points.

## Descriptive counts

There are two types of queries provided here: counts of tweets in the dataset (i.e. matching the required parameters); counts of tweets matching each keyword in the dataset.

Each of the two query types has a file with the numbers broken down by month and a file broken down by year as well as a file with the totals for the whole time period.


### Files provided

Files included with the overall matching tweet counts:
- tweet_counts.csv
- tweet_counts_monthly.csv
- tweet_counts_yearly.csv

Files included with counts of tweets which match each keyword:
- keyword_counts.csv
- keyword_counts_monthly.csv
- keyword_counts_yearly.csv


### Columns

#### Columns present in all files

- `total_tweets`: Total number of tweets
- `num_rt`: Number of retweets within the set of tweets
- `num_not_rt`: Number of tweets which aren't retweets within the set of tweets
- `num_unique_tweets`: The number of non-retweets plus the number of retweets which are retweeting tweets that aren't otherwise present - i.e. the number of unique tweets within the set of tweets, removing any duplicates caused by retweets
- `num_unique_users`: The number of twitter accounts represented in the authors of this set of tweets

Note that the two columns about unique numbers (`num_unique_tweets` and `num_unique_users`) count *within* the subset of tweets represented by that row. For the monthly and yearly files, the numbers will not add up to the broader total numbers. An example of how unique tweets are calculated is given below.

#### Columns present in monthly and/or yearly files

- `year`: The year this tweet was posted
- `month`: The month this tweet was posted

All time grouping was done in the Sydney timezone.

#### Columns present in keywords files

- `keyword`: Which keyword this group of tweets matched

Note that there are more values in this `keyword` column than there were keywords listed in the dataset parameters above. This is due to the nature of the regular expressions used having multiple variations. For example, the keyword specified as 'basin ?plan' will match either 'basin plan' or 'basinplan' in the text (after the text is converted to lowercase). The actual matched text is what is given in the `keyword` column.

### Unique tweets calculation example

Example tweets:
- Tweet A: October 2020, not a retweet
- Tweet B: October 2020, a retweet of tweet A
- Tweet C: November 2020, a retweet of tweet A

In the overall counts file and the yearly counts file, of these three tweets only tweet A would be counted among the unique tweets.

In the monthly counts file, tweets A and B between them would count one towards October's unique tweets, and tweet C would count one towards November's unique tweets.

## Contact information

digitalobservatory@qut.edu.au

https://www.digitalobservatory.net.au/
