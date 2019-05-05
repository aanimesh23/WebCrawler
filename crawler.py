#Animesh Agrawal    animesha    50254531
#Micheal Kirk       kirkmc      49847974
#Rachel Lam         rslam       24554220

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
class Crawler:
    """
    This class is responsible for scraping urls from the next available link in frontier and adding the scraped links to
    the frontier
    """

    def __init__(self, frontier):
        self.url_dict = collections.defaultdict(int)
        self.frontier = frontier
        self.DynamicDICT = collections.defaultdict(int)
        self.subdomainDict = collections.defaultdict(int)
        self.Maxlink = ('', 0)
        self.validURLs = []
        self.invalidURLs = []
        self.corpus = Corpus()

    def write_to_file(self, filename, header, contents):
        f = open(filename, "w")
        f.write(header)
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
            self.validURLs.append(url)
            logger.info("Fetching URL %s ... Fetched: %s, Queue size: %s", url, self.frontier.fetched, len(self.frontier))
            url_data = self.fetch_url(url)

            for next_link in self.extract_next_links(url_data):
                if self.corpus.get_file_name(next_link) is not None:
                    if self.is_valid(next_link):
                        self.frontier.add_url(next_link)


        ## Writing the statistics to different text files
        self.write_to_file("subdomains.txt", "Subdomains visited:\n\n", self.subdomainDict) # Subdomain : Number of links under that domain
        self.write_to_file("mostvalid.txt", "Page with most valid URLs:\n\n", self.Maxlink) # Link : Number of links on the page
        self.write_to_file("downloadedURLS.txt", "List of downloaded URLs:\n\n", self.validURLs) # All crawled links
        self.write_to_file("traps.txt", "List of identified traps:\n\n", self.invalidURLs) # All the links which were considered as traps

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
            content = f.read() # reading the contents
            s = len(content) # Size of the file
            url_data["url"] = url
            url_data["content"] = content
            url_data['size'] = s

        return url_data

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

        soup = BeautifulSoup(url_data["content"], "lxml") # parsing the contents of page
        tags = soup.find_all('a') # extracting a tags 
        for tag in tags:
            link = tag.get('href') # Extracting links in hrefs
            if type(link) != type(None): 
                link = urljoin(url_data["url"], link) #converting all links to absolute links
                outputLinks.append(link) # Adding the link to output link list to return thr file

        count = len(outputLinks) # statistics to check page with maximum links
        if self.Maxlink[1] < count:
            self.Maxlink = (url_data["url"], count)

        return outputLinks


    def is_valid(self, url):
        """
        Function returns True or False based on whether the url has to be fetched or not. This is a great place to
        filter out crawler traps. Duplicated urls will be taken care of by frontier. You don't need to check for duplication
        in this method
        """
        parsed = urlparse(url)
        if ".ics.uci.edu" in parsed.hostname: #makes sure we are only considering links in the ics.uci.edu subdomain 

            self.subdomainDict[parsed.netloc] += 1 # Number of links in a subdomain
            if parsed.scheme not in set(["http", "https"]):
                return False


            static_portion = url.split('?')[0] #extracting the static portion from a dynamic URL

            self.DynamicDICT[static_portion] += 1
            if self.DynamicDICT[static_portion] > 1000: #removes a dynamic URL if the static portion is repeated for a 1000 times
                self.invalidURLs.append(url)
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
            word, freq = Counter(paths_split).most_common(1)[0] #checks for repeating directories in a link to check for traps
            if freq > 12:
                self.invalidURLs.append(url)
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