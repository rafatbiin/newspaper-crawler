# -*- coding: utf-8 -*-

import unittest
from crawler.crawler.utils.url_processor import URLProcessor


class TestURLProcessor(unittest.TestCase):

    def test_extract_int(self):
        test_result = URLProcessor.get_domain("https://www.prothomalo.com")
        correct_result = "prothomalo.com"
        self.assertEqual(test_result, correct_result)

        test_result = URLProcessor.get_domain("http://www.prothomalo.com")
        correct_result = "prothomalo.com"
        self.assertEqual(test_result, correct_result)

        test_result = URLProcessor.get_domain("http://prothomalo.com")
        correct_result = "prothomalo.com"
        self.assertEqual(test_result, correct_result)

        test_result = URLProcessor.get_domain("http://bangla.bdnews24.com")
        correct_result = "bangla.bdnews24.com"
        self.assertEqual(test_result, correct_result)

        test_result = URLProcessor.get_domain("http://thedailystar.net")
        correct_result = "thedailystar.net"
        self.assertEqual(test_result, correct_result)


if __name__ == '__main__':
    unittest.main()
