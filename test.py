import logging
import re
from urllib.parse import urlparse
from urllib.parse import urljoin
from corpus import Corpus
import lxml.html
from collections import Counter
from bs4 import BeautifulSoup

from lxml import etree
from io import StringIO, BytesIO

def extract_next_links(self, url_data):
	outputLinks = []

    soup = BeautifulSoup(url_data["content"], "lxml")
    tags = soup.find_all('a')

    for tag in tags:
            link = tag.get('href')
            if type(link) != type(None):
                
                #check for links not starting with http or / then adds base url with additional backslash to link
                if len(link) > 0 and link[0] != "h":
                    link = urljoin(url_data["url"], link)

                # if current link is relative then add base url to it (relative = /blah instead of having proper protocol)
                if len(link) > 0 and link[0] == "/":
                    link = urljoin(url_data["url"], link)

                #remove backslash from end of link
                if len(link) > 0 and link[-1] == "/":
                    link = link[:-1]

                outputLinks.append(link)

    return outputLinks

urljoin(url_data["url"], link)