import logging
import time

from selenium import webdriver
from bs4 import BeautifulSoup


BASE_URL = 'https://portal.librus.pl/szkola/synergia/loguj'
FIRST_PAGE = 'https://mbopn.kuratorium.waw.pl/#/'
NEXT_PAGE_PATTERN_SUFFIX = 'page/'