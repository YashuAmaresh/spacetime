import logging
from datamodel.search.datamodel import ProducedLink, OneUnProcessedGroup, robot_manager
from spacetime_local.IApplication import IApplication
from spacetime_local.declarations import Producer, GetterSetter, Getter
from lxml import html,etree
import re, os
from time import time

try:
    # For python 2
    from urlparse import urlparse, parse_qs, urljoin
    already_visited = set()
except ImportError:
    # For python 3
    from urllib.parse import urlparse, parse_qs


logger = logging.getLogger(__name__)
LOG_HEADER = "[CRAWLER]"
url_count = 0 if not os.path.exists("successful_urls.txt") else (len(open("successful_urls.txt").readlines()) - 1)
if url_count < 0:
    url_count = 0
MAX_LINKS_TO_DOWNLOAD = 20

@Producer(ProducedLink)
@GetterSetter(OneUnProcessedGroup)
class CrawlerFrame(IApplication):

    def __init__(self, frame):
        self.starttime = time()
        # Set app_id <student_id1>_<student_id2>...
        self.app_id = "31721795_50924931_85241493"
        # Set user agent string to IR W17 UnderGrad <student_id1>, <student_id2> ...
        # If Graduate studetn, change the UnderGrad part to Grad.
        self.UserAgentString = "IR W17 Grad 31721795 50924931 85241493"
		
        self.frame = frame
        assert(self.UserAgentString != None)
        assert(self.app_id != "")
        if url_count >= MAX_LINKS_TO_DOWNLOAD:
            self.done = True

    def initialize(self):
        self.count = 0
        l = ProducedLink("http://www.ics.uci.edu", self.UserAgentString)
        print l.full_url
        self.frame.add(l)

    def update(self):
        for g in self.frame.get(OneUnProcessedGroup):
            print "Got a Group"
            outputLinks = process_url_group(g, self.UserAgentString)
            for l in outputLinks:
                if is_valid(l) and robot_manager.Allowed(l, self.UserAgentString):
                    lObj = ProducedLink(l, self.UserAgentString)
                    self.frame.add(lObj)
        if url_count >= MAX_LINKS_TO_DOWNLOAD:
            self.done = True

    def shutdown(self):
        print "downloaded ", url_count, " in ", time() - self.starttime, " seconds."
        pass

def save_count(urls):
    global url_count
    url_count += len(urls)
    with open("successful_urls.txt", "a") as surls:
        surls.write("\n".join(urls) + "\n")

def process_url_group(group, useragentstr):
    rawDatas, successfull_urls = group.download(useragentstr, is_valid)
    save_count(successfull_urls)
    return extract_next_links(rawDatas)
    
#######################################################################################
'''
STUB FUNCTIONS TO BE FILLED OUT BY THE STUDENT.
'''
def extract_next_links(rawDatas):
    outputLinks = list()
    from bs4 import BeautifulSoup
    from lxml.html import soupparser

    for data in rawDatas:
        curr_url = data[0]
        htmlStr = data[1]

        if htmlStr:

            # BeautifulSoup(htmlStr, "html.parser")

            '''
            Using BeautifulSoup Parser to auto-detect the encoding of the HTML content
            '''

            root = html.fromstring(htmlStr)
            try:
                ignore = html.tostring(root, encoding='unicode')

            except UnicodeDecodeError:
                root = html.soupparser.fromstring(htmlStr)
            # dom = soupparser.fromstring(htmlStr)
            # dom =  html.fromstring(htmlStr)
            # print dom.xpath('//a/@href')
            for link in root.xpath('//a/@href'): # select the url in href for all a tags(links)
                print link

            links = root.xpath('//a/@href')
            absoluteLinks = convertToAbsolute(curr_url, links)

    # print rawDatas
    '''
    rawDatas is a list of tuples -> [(url1, raw_content1), (url2, raw_content2), ....]
    the return of this function should be a list of urls in their absolute form
    Validation of link via is_valid function is done later (see line 42).
    It is not required to remove duplicates that have already been downloaded. 
    The frontier takes care of that.

    Suggested library: lxml
    '''
    return outputLinks

def is_valid(url):
    '''
    Function returns True or False based on whether the url has to be downloaded or not.
    Robot rules and duplication rules are checked separately.

    This is a great place to filter out crawler traps.
    '''

    try:
        already_visited

    except NameError:
        already_visited = set()

    parsed = urlparse(url)
    if parsed.scheme not in set(["http", "https"]):
        return False
    try:
        return_val = True


        return_val = ".ics.uci.edu" in parsed.hostname \
            and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4"\
            + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
            + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
            + "|thmx|mso|arff|rtf|jar|csv"\
            + "|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

        print "Parsed hostname : ", parsed.hostname, " : ", return_val
        '''
        Check here for crawler traps
        '''
        # 1. Repeating directories
        if re.match("^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$", parsed.path.lower()):
            return_val = False

        # 2. Calendar traps - Keep track of already visited paths
        elif parsed.netloc.lower() + "/" + parsed.path.lower().lstrip("/") in already_visited:
            return_val = False

        #Add the current URL path to set of already visited paths 
        else: 
            already_visited.add(parsed.netloc.lower() + "/" + parsed.path.lower().lstrip("/"))
            return_val = True

        return return_val

    except TypeError:
        print ("TypeError for ", parsed)


def convertToAbsolute(url, links):
    '''
        <scheme>://<username>:<password>@<host>:<port>/<path>;<parameters>?<query>#<fragment>
        Not handled mailto and fragments(#)
        Also, javascript needs to be handled
    '''
    parsed_url = urlparse(url)
    base_url = parsed_url.scheme +"://"+ parsed_url.netloc + parsed_url.path
    absolutelinks = list()
    for link in links:
        link = link.strip()

        if link.find('http') == 0:
            absolutelinks.append(link)

        elif link.find('//') == 0:
            absolutelinks.append(link)

        elif link.find('#') == 0 or link.find("javascript") == 0 or link.find("mailto") == 0: #****
            pass

        elif link.find("/") == 0:
            if re.match(".*\.(asp|aspx|axd|asx|asmx|ashx|css|cfm|yaws|swf|html|htm|xhtml" \
                + "|jhtmljsp|jspx|wss|do|action|js|pl|php|php4|php3|phtml|py|rb|rhtml|shtml|xml|rss|svg|cgi|dll)$", parsed_url.path.lower()):
                # print "\n\n\n\nHere\n\n\n\n"
                index = parsed_url.path.rfind("/")
                parent_path = parsed_url.path[:index]
                result = parsed_url.scheme +"://"+ parsed_url.netloc + parent_path + link

            else:
                result = parsed_url.scheme +"://"+ parsed_url.netloc + parsed_url.path.rstrip("/") + link

            absolutelinks.append(result)

        else:

            absolutelinks.append(urljoin(base_url,link))
    
    print base_url
    
    for urls in absolutelinks:
        print "Link= " + urls +"\n" 

















