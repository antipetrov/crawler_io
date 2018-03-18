# coding: utf-8
__author__ = 'petrmatuhov'

import unittest
import os
from ycrawler import *


class YCrawlerTestcase(unittest.TestCase):

    # def test_save_to_file(self):
    #     root_url = 'http://ya.ru'
    #     url = 'http://google.com'
    #     test_content = 'test strs'
    #
    #     test_dirname = os.path.join(RESULTS_DIR, root_url)
    #     test_filename = os.path.join(test_dirname, url)
    #
    #     try:
    #         os.unlink(test_filename)
    #         os.rmdir(test_dirname)
    #
    #     except Exception as e:
    #         pass
    #
    #     save_to_file(root_url, url, test_content)
    #
    #     dir_created = os.path.isdir(test_dirname)

    def test_parse_news_page(self):
        with open('test/test_news.html', 'rb') as html_file:
            page_html = html_file.read()

        links = parse_news_page(page_html)
        print(links)

        self.assertEqual(len(links), 5)


if __name__ == '__main__':
    unittest.main()