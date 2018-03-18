#-*- coding: utf-8 -*-

import asyncio
import aiohttp
import async_timeout
from datetime import datetime

# import argparse
import logging
import async_timeout
import re
import os
import html
from urllib.parse import quote, unquote, urlencode

REQUEST_TIMEOUT = 3.0
RESCAN_NEWS_TIMEOUT = 60
INDEX_URL = 'http://news.ycombinator.com/'
NEWS_PATTERN = '<td class="title"><a href="(\S+)" class="storylink">'
INDEX_LINK_PATTERN = '<span class="age"><a href="(item\S+)">[^<]*</a>'
TITLE_PATTERN = '<td class="title"><a href="(http\S+)"'
COMMENT_LINK_PATTERN = '<a href="((http|https):&#x2F;&#x2F\S+)"'
RESULTS_DIR = 'results'

# parser = argparse.ArgumentParser(
#     description='Crawler for ycombinator news')

# parser.add_argument('--verbose', action='store_true', help='Detailed output')

LOGGER_FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=LOGGER_FORMAT, datefmt='[%H:%M:%S]')
log = logging.getLogger()
log.setLevel(logging.INFO)



class URLFetcher(object):

    def __init__(self, session):
        self.session = session
        self.last_request_time = None

    async def fetch(self, url):
        if self.last_request_time:
            time_diff = (datetime.now() - self.last_request_time).total_seconds()
            if time_diff < REQUEST_TIMEOUT:
               await asyncio.sleep(REQUEST_TIMEOUT - time_diff)

        async with self.session.get(url) as response:
            log.info('fetch start time {}'.format(datetime.now()))
            self.last_request_time = datetime.now()
            return await response.read()


def parse_index(html_bytes):
    html_str = str(html_bytes)
    links = re.findall(INDEX_LINK_PATTERN, html_str)
    return [html.unescape(l) for l in links]


def parse_news_page(html_pytes):
    html_str = str(html_pytes)
    title_links = re.findall(TITLE_PATTERN, html_str)

    # rebuilding list - there are 2 groups in coment-link-pattern
    comment_links = [l[0] for l in re.findall(COMMENT_LINK_PATTERN, html_str)]
    all_links = title_links + comment_links

    return [html.unescape(l) for l in all_links]


async def async_process_index(fetcher, url):
    print('loading news links {}'.format(url))
    news_page_links = parse_index(await fetcher.fetch(url))
    return news_page_links


async def async_process_page(fetcher, page_link):
    comment_links = parse_news_page(await fetcher.fetch(INDEX_URL+page_link))
    log.info('page {}: {} links found'.format(INDEX_URL+page_link, len(comment_links)))

    saved_count = 0
    for link in comment_links:
        saved = await async_download_url(fetcher, page_link, link)
        if saved:
            saved_count += 1

    return True


async def async_download_url(fetcher, news_url, url):
    dirname = news_url.replace('item?id=')
    saved = save_to_file(dirname, url, await fetcher.fetch(url))
    log.info('saved {}/{}'.format(dirname, url))

    return saved


def save_to_file(dir, url, content):

    safe_filename = quote(url[url.find('://')+3:].replace('/','-'),'')
    target_dirname = os.path.join(RESULTS_DIR, quote(dir, ''))
    target_filename = os.path.join(target_dirname, safe_filename)

    # check dir
    if not os.path.isdir(target_dirname):
        try:
            os.mkdir(target_dirname)
        except Exception as e:
            log.exception('Error creating directory {}'.format(target_dirname))
            raise

    # writing content to file
    try:
        with open(target_filename, 'wb') as target_file:
            target_file.write(content)
    except Exception as e:
        log.exception("Error writing file {} into {}".format(target_filename, target_dirname))
        raise

    return True


async def main_dispatcher(loop, session):
    errors = []
    news_tasks = {}
    fetcher = URLFetcher(session)
    while True:
        if errors:
            log.info('Error detected, quitting')
            return

        index_links_future = asyncio.ensure_future(async_process_index(fetcher, INDEX_URL))

        def on_news_list_loaded(future):
            try:
                news_links = future.result()
            except Exception as e:
                log.exception('Error loading index')
                news_links = []

            for link in news_links:
                if not news_tasks.get(link):
                    news_tasks[link] = asyncio.ensure_future(async_process_page(fetcher, link))


        index_links_future.add_done_callback(on_news_list_loaded)

        # периодически проверяем - нет ли новых новостей
        await asyncio.sleep(RESCAN_NEWS_TIMEOUT)
        log.info('sceduled rescan in {} sec'.format(RESCAN_NEWS_TIMEOUT))

    return True


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    with aiohttp.ClientSession(loop=loop) as session:
        loop.run_until_complete(main_dispatcher(loop, session))
    
    loop.close()
