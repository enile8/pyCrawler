#!/usr/bin/python
import sys
import re
import urllib2
import urlparse
import threading
import MySQLdb
import robotparser
from BeautifulSoup import BeautifulSoup
import Settings
# Try to import psyco for JIT compilation
try:
	import psyco
	psyco.full()
except ImportError:
	print "Continuing without psyco JIT compilation..."

"""
The program should take arguments
1) start url
2) crawl depth 
3) verbose (optional)
Start out by checking to see if the args are there and
set them to their variables
"""
if len(sys.argv) < 3:
	sys.exit("Not enough arguments!")
else:
	starturl = sys.argv[1]
	crawldepth = int(sys.argv[2])
if len(sys.argv) == 5:
	if (sys.argv[3].upper() == "TRUE"):
		verbose = True
	else:
		verbose = False
else:
	verbose = False
# urlparse the start url
surlparsed = urlparse.urlparse(starturl)

# Connect to the db and create the tables if they don't already exist
try:
	connection = MySQLdb.connect(host = Settings.serverhost, user = Settings.username, passwd = Settings.password, db = Settings.database)
except:
	connection = MySQLdb.connect(host = Settings.serverhost, user = Settings.username, passwd = Settings.password)
	c = connection.cursor()
	#create the database if it doesn't exist
	c.execute('CREATE DATABASE IF NOT EXISTS %s'% Settings.database)
	#select the database
	c.execute('USE %s'% Settings.database)
	# crawl_index: holds all the information of the urls that have been crawled
	c.execute('CREATE TABLE IF NOT EXISTS crawl_index (crawlid INTEGER PRIMARY KEY, parentid INTEGER, url VARCHAR(256), title VARCHAR(256), keywords VARCHAR(256) )')
	# queue: this should be obvious
	c.execute('CREATE TABLE IF NOT EXISTS queue (id INTEGER PRIMARY KEY AUTO_INCREMENT, parent INTEGER, depth INTEGER, url VARCHAR(256))')
	# status: Contains a record of when crawling was started and stopped. 
	# Mostly in place for a future application to watch the crawl interactively.
	c.execute('CREATE TABLE IF NOT EXISTS status ( s INTEGER, t VARCHAR(256) )')
#Database connection settings, probably a better way of doing this but that's what I have for now
connection = MySQLdb.connect(host = Settings.serverhost, user = Settings.username, passwd = Settings.password, db = Settings.database)
c = connection.cursor()
#Link regex expression
linkregex = re.compile('<a.*\shref=[\'"](.*?)[\'"].*?>')
crawled = []

# set crawling status and stick starting url into the queue
c.execute("INSERT INTO status VALUES (%s, %s)", (1, "datetime('now')"))
c.execute("INSERT INTO queue VALUES (%s, %s, %s, %s)", (None, 0, 0, starturl))

# insert starting url into queue

class threader ( threading.Thread ):
	
	# Parser for robots.txt that helps determine if we are allowed to fetch a url
	rp = robotparser.RobotFileParser()
	
	"""
	run()
	Args:
		none
	the run() method contains the main loop of the program. Each iteration takes the url
	at the top of the queue and starts the crawl of it. 
	"""
	def run(self):
		while 1:
			try:
				# Get the first item from the queue
				c.execute("SELECT * FROM queue LIMIT 1")
				crawling = c.fetchone()
				# Remove the item from the queue
				c.execute("DELETE FROM queue WHERE id = %s", (crawling[0], ))
				
				if verbose:
					print crawling[3]
			except KeyError:
				raise StopIteration
			except:
				pass
			
			# if theres nothing in the que, then set the status to done and exit
			if crawling == None:
				c.execute("INSERT INTO status VALUES (%s, %s)", (0, "datetime('now')"))
				
				sys.exit("Done!")
			# Crawl the link
			self.crawl(crawling)
		
	"""
	crawl()
	Args:
		crawling: this should be a url
	
	crawl() opens the page at the "crawling" url, parses it and puts it into the database.
	It looks for the page title, keywords, and links.
	"""
	def crawl(self, crawling):
		# crawler id
		cid = crawling[0]
		# parent id. 0 if start url
		pid = crawling[1]
		# current depth
		curdepth = crawling[2]
		# crawling urL
		curl = crawling[3]
		# Split the link into its sections
		url = urlparse.urlparse(curl)
		
		try:
			# Have our robot parser grab the robots.txt file and read it
			self.rp.set_url('http://' + url[1] + '/robots.txt')
			self.rp.read()
		
			# If we're not allowed to open a url, return the function to skip it
			if not self.rp.can_fetch('PyCrawler', curl):
				if verbose:
					print curl + " not allowed by robots.txt"
				return
		except:
			pass
			
		try:
			# Add the link to the already crawled list
			crawled.append(curl)
		except MemoryError:
			# If the crawled array is too big, deleted it and start over
			del crawled[:]
		try:
			# Create a Request object
			request = urllib2.Request(curl)
			# Add user-agent header to the request
			request.add_header("User-Agent", "PyCrawler")
			# Build the url opener, open the link and read it into msg
			opener = urllib2.build_opener()
			msg = opener.open(request).read()
			soup = BeautifulSoup(msg)
			
		except:
			# If it doesn't load, skip this url
			return
		
		# Find what's between the title tags
		title = soup.find("title").renderContents()
			
		# Start keywords list with whats in the keywords meta tag if there is one
		keywordregex = soup.find(attrs={"name":"keywords"})
		keywordlist = keywordregex.get("content")
		if len(keywordlist) > 0:
			keywordlist = keywordlist
		else:
			keywordlist = ""
			
		
			
		# Get the links
		links = linkregex.findall(msg)
		# queue up the links
		self.queue_links(url, links, cid, curdepth)

		try:
			# Put now crawled link into the db
			c.execute("INSERT INTO crawl_index VALUES( %s, %s, %s, %s, %s )", (cid, pid, curl, title, keywordlist))
			
		except:
			pass
			
			
	def queue_links(self, url, links, cid, curdepth):
		if curdepth < crawldepth:
			# Read the links and inser them into the queue
			for link in links:
				c.execute("SELECT url FROM queue WHERE url=%s", [link])
				for row in c:
					if row[0].decode('utf-8') == url:
						continue
				if link.startswith('/'):
					link = 'http://' + url[1] + link
				elif link.startswith('#'):
					continue
				elif not link.startswith('http'):
					link = urlparse.urljoin(url.geturl(),link)
				
				if link.decode('utf-8') not in crawled:
					try:
						c.execute("INSERT INTO queue VALUES ( %s, %s, %s, %s )", (None, cid, curdepth+1, link))
						
					except:
						continue
		else:
			pass
if __name__ == '__main__':
	# Run main loop
	threader().run()
