#!/usr/bin/env py.test

"""Unit tests for mediawords.util.twitter."""

import json
import os
from typing import List
from urllib.parse import urlparse, parse_qs
import unittest

import httpretty

import mediawords.util.config
import mediawords.util.twitter as mut

MIN_TEST_TWEET_LENGTH = 10
MIN_TEST_TWITTER_USER_LENGTH = 3


def _mock_users_lookup(request, uri, response_headers) -> List:
    """Mock twitter /statuses/lookup response."""
    params = parse_qs(request.body.decode('utf-8'))

    screen_names = params['screen_name'][0].split(',')

    users = []
    for i, screen_name in enumerate(screen_names):
        user = {
            'id': str(i),
            'name': 'user %d' % i,
            'screen_name': screen_name,
            'description': "test description for user %d" % i}
        users.append(user)

    return [200, response_headers, json.dumps(users)]


def test_fetch_100_users() -> None:
    """Test fetch_100_tweets using mock."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.POST, "https://api.twitter.com/1.1/users/lookup.json", body=_mock_users_lookup)

    got_users = mut.fetch_100_users(['foo', 'bar', 'bat'])

    got_screen_names = [u['screen_name'] for u in got_users]

    assert sorted(got_screen_names) == ['bar', 'bat', 'foo']

    httpretty.disable()
    httpretty.reset()


def _mock_statuses_lookup(request, uri, response_headers) -> List:
    """Mock twitter /statuses/lookup response."""
    params = parse_qs(urlparse(uri).query)

    ids = params['id'][0].split(',')

    json = ','.join(['{"id": %s, "text": "content %s"}' % (id, id) for id in ids])

    json = '[%s]' % json

    return [200, response_headers, json]


def test_fetch_100_tweets() -> None:
    """Test fetch_100_tweets using mock."""
    httpretty.enable()
    httpretty.register_uri(
        httpretty.GET, "https://api.twitter.com/1.1/statuses/lookup.json", body=_mock_statuses_lookup)

    got_tweets = mut.fetch_100_tweets([1, 2, 3, 4])

    assert sorted(got_tweets, key=lambda t: t['id']) == [
        {'id': 1, 'text': "content 1"},
        {'id': 2, 'text': "content 2"},
        {'id': 3, 'text': "content 3"},
        {'id': 4, 'text': "content 4"}]

    httpretty.disable()
    httpretty.reset()


def test_get_tweet_urls() -> None:
    """Test get_tweet_urls()."""
    tweet = {'entities': {'urls': [{'expanded_url': 'foo'}, {'expanded_url': 'bar'}]}}
    urls = mut.get_tweet_urls(tweet)
    assert sorted(urls) == ['bar', 'foo']

    tweet = \
        {
            'entities':
                {
                    'urls': [{'expanded_url': 'url foo'}, {'expanded_url': 'url bar'}],
                },
            'retweeted_status':
                {
                    'entities':
                        {
                            'urls': [{'expanded_url': 'rt url foo'}, {'expanded_url': 'rt url bar'}],
                        }
                }
        }
    urls = mut.get_tweet_urls(tweet)
    expected_urls = ['url bar', 'url foo', 'rt url foo', 'rt url bar']
    assert sorted(urls) == sorted(expected_urls)
