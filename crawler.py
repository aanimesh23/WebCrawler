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
import collections

logger = logging.getLogger(__name__)
DynamicDICT = collections.defaultdict(int)
subdomainDict = collections.defaultdict(int)
Maxlink = ('', 0)
validURLs = []
invalidURLs = []
class Crawler:
    """
    This class is responsible for scraping urls from the next available link in frontier and adding the scraped links to
    the frontier
    """

    def __init__(self, frontier):
        self.url_dict = collections.defaultdict(int)
        self.frontier = frontier
        self.corpus = Corpus()

    def write_to_file(self, filename, header, contents):
        f = open(filename, "w")
        f.write(header)
        print(type(contents))
        if type(contents) is list:
            for item in contents:
                f.write(str(item) + "\n")
        elif type(contents) is tuple:
            f.write(str(contents[0]) + " " + str(contents[1]) + "\n")
        else:
            for key,value in contents.items():
                f.write(str(key) + ": " + str(value) + "\n")
        f.close()

    def start_crawling(self):
        """
        This method starts the crawling process which is scraping urls from the next available link in frontier and adding
        the scraped links to the frontier
        """
        while self.frontier.has_next_url():
            url = self.frontier.get_next_url()
            validURLs.append(url)
            logger.info("Fetching URL %s ... Fetched: %s, Queue size: %s", url, self.frontier.fetched, len(self.frontier))
            url_data = self.fetch_url(url)

            for next_link in self.extract_next_links(url_data):
                #print(next_link)
                if self.corpus.get_file_name(next_link) is not None:
                    if self.is_valid(next_link):
                        self.frontier.add_url(next_link)

        self.write_to_file("subdomains.txt", "Subdomains visited:\n\n", subdomainDict)
        self.write_to_file("mostvalid.txt", "Page with most valid URLs:\n\n", Maxlink)
        self.write_to_file("downloadedURLS.txt", "List of downloaded URLs:\n\n", validURLs)
        self.write_to_file("traps.txt", "List of identified traps:\n\n", invalidURLs)

    def fetch_url(self, url):
        """
        This method, using the given url, should find the corresponding file in the corpus and return a dictionary
        containing the url, content of the file in binary format and the content size in bytes
        :param url: the url to be fetched
        :return: a dictionary containing the url, content and the size of the content. If the url does not
        exist in the corpus, a dictionary with content set to None and size set to 0 can be returned.
        """
        url_data = {
            "url": url,
            "content": None,
            "size": 0
        }

        file = self.corpus.get_file_name(url) # Get URL from the corpus
        if file == None:
            return url_data

        try:
            f = open(file, "rb") # Open the file to get the content
        except(Exception):
            return url_data
        else:
            content = f.read()
            s = len(content)
            url_data["url"] = url
            url_data["content"] = content
            url_data['size'] = s

        return url_data

    def make_links_absolute(soup, url):
        for tag in soup.findAll('a', href=True):
            tag['href'] = urljoin(url, tag['href'])

    def extract_next_links(self, url_data):
        """
        The url_data coming from the fetch_url method will be given as a parameter to this method. url_data contains the
        fetched url, the url content in binary format, and the size of the content in bytes. This method should return a
        list of urls in their absolute form (some links in the content are relative and needs to be converted to the
        absolute form). Validation of links is done later via is_valid method. It is not required to remove duplicates
        that have already been fetched. The frontier takes care of that.

        Suggested library: lxml
        """
        
        outputLinks = []

        soup = BeautifulSoup(url_data["content"], "lxml")
        tags = soup.find_all('a')
        for tag in tags:
            link = tag.get('href')
            if type(link) != type(None):
                link = urljoin(url_data["url"], link)
                outputLinks.append(link)

        count = len(outputLinks)
        global Maxlink
        if Maxlink[1] < count:
            Maxlink = (url_data["url"], count)

        return outputLinks


    def is_valid(self, url):
        """
        Function returns True or False based on whether the url has to be fetched or not. This is a great place to
        filter out crawler traps. Duplicated urls will be taken care of by frontier. You don't need to check for duplication
        in this method
        """
        parsed = urlparse(url)

        subdomainDict[parsed.netloc] += 1
        if parsed.scheme not in set(["http", "https"]):
            return False


        static_portion = url.split('?')[0]

        DynamicDICT[static_portion] += 1
        if DynamicDICT[static_portion] > 1000:
            invalidURLs.append(url)
            return False

        #check duplicate links with variance of http vs. https ()
        # if url[:5] == "http:":
        #     if self.url_dict[url[4:]] > 0:
        #         return False
        #     else:
        #         self.url_dict[url[4:]] += 1
        # elif url[:5] == "https":
        #     if self.url_dict[url[5:]] > 0:
        #         return False
        #     else:
        #         self.url_dict[url[5:]] += 1

        paths_split = parsed.path.split("/")
        word, freq = Counter(paths_split).most_common(1)[0]
        if freq > 15:
            invalidURLs.append(url)
            return False

        try:
            return ".ics.uci.edu" in parsed.hostname \
                   and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4" \
                                    + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
                                    + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
                                    + "|thmx|mso|arff|rtf|jar|csv" \
                                    + "|rm|smil|wmv|swf|wma|zip|rar|gz|pdf)$", parsed.path.lower())

        except TypeError:
            print("TypeError for ", parsed)
            return False