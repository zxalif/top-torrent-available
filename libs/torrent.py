#!/usr/bin/python3

import requests
import bs4 as bs

TRENDING_MOVIES = "https://1337x.to/trending/d/movies/"
TOP_MOVIES = "https://1337x.to/top-100-movies"


def get_response(url):
    try:
        response = requests.get(url)
        data = response.text
    except requests.exceptions.ConnectionError:
        data = ''
    return data


def extract(soup):
    trs = soup.findAll("tr")[1:]
    data = []
    for tr in trs:
        name = tr.find('td', {'class': 'name'})
        name = name.text.split('\n')[-1]
        size = tr.find('td', {'class': 'size'}).text
        seeds = tr.find('td', {'class': 'seeds'}).text
        leeches = tr.find('td', {'class': 'leeches'}).text
        coll_date = tr.find('td', {'class': 'coll-date'}).text
        size = tr.find('td', {'class': 'size'}).text
        data.append(dict(
            name=name,
            size=size.rstrip(seeds),
            se=seeds,
            le=leeches,
            time=coll_date,
            type='movie',
        ))

    return data


def get_trending_movies():
    response = get_response(TRENDING_MOVIES)
    soup = bs.BeautifulSoup(response, 'html.parser')
    return extract(soup)


def get_top_movies():
    response = get_response(TOP_MOVIES)
    soup = bs.BeautifulSoup(response, 'html.parser')
    return extract(soup)

# res = requests.post(
#     "https://hooks.slack.com/services/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",
#     json={"text": '```' + "\n".join(data) + '```'}, headers={"Conent-Type": "application/json"})
