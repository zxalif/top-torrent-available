#!/usr/bin/python3

import requests
import bs4 as bs


TRENDING_MOVIES = "https://1337x.to/trending/d/movies/"
TOP_MOVIES = "https://1337x.to/top-100-movies"


def get_response(url, raw=False):
    try:
        response = requests.get(url)
        data = response.content if raw else response.text
    except requests.exceptions.ConnectionError:
        data = ''
    return data


def extract(soup):
    trs = soup.findAll("tr")[1:]
    data = []
    for tr in trs:
        name = tr.find('td', {'class': 'name'})
        url = name.findAll('a')[-1]['href']
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
            url=url,
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


def download_related(link):
    if not link: return {}
    url = 'https://1337x.to{}'.format(link)
    respone = get_response(url)
    soup = bs.BeautifulSoup(respone, 'html.parser')
    return extract(soup)


def get_details(link):
    if not link: return {}
    url = 'https://1337x.to{}'.format(link)
    respone = get_response(url)
    soup = bs.BeautifulSoup(respone, 'html.parser')
    _name = soup.find('h3')
    if not _name: return {}
    name = _name.text
    has_related = None
    if name == 'Code: ':
        name = soup.find('h1').text
    else:
        has_related = _name.find('a')
        has_related = has_related['href'] if has_related else None
    se = soup.find('span', {'class': 'seeds'}).text
    le = soup.find('span', {'class': 'leeches'}).text
    keywords = soup.find('div', {'class': 'torrent-category'}) or []
    if keywords:
        keywords = [span.text for span in keywords.findAll('span')]
    downloads = soup.find(lambda tag: tag.name == 'li' and 'Downloads' in tag.text).find('span').text
    category = soup.find(lambda tag: tag.name == 'li' and 'Category' in tag.text).find('span').text
    languages = soup.find(lambda tag: tag.name == 'li' and 'Language' in tag.text).find('span').text
    size = soup.find(lambda tag: tag.name == 'li' and 'Total size' in tag.text).find('span').text
    image = soup.find('div', {'class': 'torrent-image'})
    if image:
        image = image.find('img')
        if image:
            image = 'https:{}'.format(image['src'])
    magnet = soup.find(lambda tag: tag and tag.name == 'a' and 'Magnet Download' in tag.text)
    data = dict(
        name=name,
        se=se,
        le=le,
        keywords=keywords,
        downloads=downloads,
        category=category,
        languages=languages,
        size=size,
        image=image,
        magnet=magnet['href'] if magnet else '',
        has_related=has_related,
    )
    return data


def download_image(link):
    if not link: return False
    response = get_response(link, raw=True)
    with open("img/tmp", "wb") as img:
        img.write(response)
    return True
