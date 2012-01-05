Setup
=====
- Open Settings.py and complete MySQL database settings
- Next open terminal to the directory that holds the crawler and enter commands
- start url
- crawl depth 
- verbose (this command is optional)
- The final command should look something like:
- ./crawler.py http://example.com 1

Current State
=============
- The crawler hasn't really been tested, just a little practice project. The content that was crawled was "clean" html, but should work with other pages as well.
- Most of everything that is currently completed by the crawler could be done with the standard library, but BeautifulSoup is used for future expansion to get keywords incase there is no meta keywords (which is very common).
- The current database setup, checking of setup is very poor and needs work. If there is a database by the name you enter already created it will currently skip checking for tables which = Errors.

Dependencies
============
- [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/)
- [MySQLdb](http://sourceforge.net/projects/mysql-python/)

Feature Plans
=============
- Add a Readability like extension in order to try and extract the main content of the page
- Add NLTK support for a greater understanding of the webpage

Props
=====
Thanks to [Ryan Merl](https://github.com/theanti9), this project was a fork of an earlier version of his [PyCrawler](https://github.com/theanti9/PyCrawler).
