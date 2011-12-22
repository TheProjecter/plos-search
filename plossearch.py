'''
   Author: Bill OConnor 
   Description: Command line tools for PLoS search API

   The Public Library of Science (PLoS) publishes peer 
   reviewed research under the Creative Commons license. 
   All articles are available to the public free of charge. 
   Info regarding the RESTful web API to the PLoS Solr based 
   search engine is available at http://api.plos.org. 
   
   This is a collection of python modules and commandline 
   tools to aid in using this api. 

   License: http://www.opensource.org/licenses/mit-license.php

'''
import json
from optparse import OptionParser
from urllib2  import urlopen, quote, unquote
	
__version__ = "0.0.1"
__all__ = ['articleUrl', 'articleXML', 'PlosSearch']

_searchUrl = 'http://api.plos.org/search?'
'''
   _JMap - map a journal name to a url.
'''
_JMap = {
		'PLoS Biology'               : 'http://www.plosbiology.org',
		'PLoS Genetics'              : 'http://www.plosgenetics.org',
		'PLoS Computational Biology' : 'http://www.ploscompbiol.org',
		'PLoS Medicine'              : 'http://www.plosmedicine.org',
		'PLoS ONE'                   : 'http://www.plosone.org',
		'PLoS Neglected Tropical Diseases' : 'http://www.plosntds.org',
		'PLoS Clinical Trials'       : 'http://clinicaltrials.ploshubs.org',
		'PLoS Pathogens'             : 'http://www.plospathogens.org'
	    }
'''
   _JIds - map a 4 character journal id to quoted journal name.
'''
_JIds = {
		'pbio' : '"PLoS Biology"',
		'pgen' : '"PLoS Genetics"',
		'pcbi' : '"PLoS Computational Biology"',
		'pmed' : '"PLoS Medicine"',
		'pone' : '"PLoS ONE"',
		'pntd' : '"PLoS Neglected Tropical Diseases"',
		'pctr' : '"PLoS Clinical Trials"',
		'ppat' : '"PLoS Pathogens"'
	}	

def articleUrl(doi,jid):
    '''
		articleUrl- return a valid link to the article page given the journal
		            4 character identifier and the article doi.
    '''
    return _JMap[jid] + '/article/' + quote('info:doi/' + doi)

def articleXML(doi,jid):
    '''
		articleXML - return a valid link to the article XML give the journal
		             4 character identifier and the article doi.
    '''
    return _JMap[jid] + '/article/fetchObjectAttachment.action?uri=' + quote('info:doi/' + doi) +\
           '&representation=XML'
    
def mkQueryUrl(url, query):
    '''	
		mkQuery - given a url and a dictionary of parameters keys and values
        		  create a valid url query string.
    '''
    paramList = [ "%s=%s" % (k, quote(v)) for k,v in query.iteritems()]
    return url + "&".join(paramList) 
	
class PlosSearch:
    '''
        PlosSearch - provides basic framework to access PLoS http://api.plos.org.
                     
    '''
    def __init__(self, api_key, jrnls=None, start=0, limit=99, maxRows=50, verbose=False):
        self.start = start; self.limit = limit; self.api_key = api_key
        self.verbose = verbose; self.cursor = -1
        self.maxRows = limit if limit < maxRows else maxRows
        self.query = {
					'start': str(self.start),
                    'rows': str(self.maxRows),
                    'fq': 'doc_type:full AND !article_type_facet:"Issue Image"',
                    'wt': 'json',
                    'api_key': api_key,
                   } 
        if jrnls:
            query['journal'] = '(' + ' OR '.join( [_JIds[j] for j in jrnls] ) + ')'
            
        self.docs = []; self.status = -1; self.QTime = -1; self.numFound = 0
                
    # Iterator Protocol       
    def __iter__(self):
        return self
       
    def next(self):
        self.cursor += 1
        if self.cursor == len(self.docs):
            self.start += self.cursor
            rows = self.maxRows
            if (self.start >= self.limit) or (self.start >= self.numFound):
                raise StopIteration

            if (self.start + self.maxRows) > self.limit:
               rows = self.limit - self.start
            
            self.cursor = 0
            self.query['start'] = str(self.start)
            self.query['rows'] = str(rows)
            self.search(None, None, iterate=True)

        return self.docs[self.cursor]

    def __getitem__(self):
        return self.docs[self.cursor]
                         
    def _doQuery(self, query):
        '''
        '''
        url = mkQueryUrl(_searchUrl, query )
        j = json.load(urlopen(url))
        return (j['responseHeader'],j['response'], url)
	
    def search(self, args, fields, iterate=False):
		'''
			search - returns a list of documents. 
			    args   - a list of strings specifying the query to preform.
			    
			    fields - return fields to be included in the search results.
			    
			    iterate - if iterate is true skip building a new query and
			              re-submit the request. Only used when the row limit
			              is larger than maxRows.
		'''
		# If we are iterating skip the assembling the query.
		if not iterate:
			if len(args) > 0:
				self.query['q'] = " AND ".join(args)	   
			self.query['fl'] = fields 

		(header, resp, url) = self._doQuery(self.query)
		self.status = header['status']; self.QTime = header['QTime']
		self.numFound = resp['numFound']
		self.docs = resp['docs']
                
		if self.verbose: 
			print 'Query url: ' + unquote(url) 
			print 'Status: %s\nQTIme: %s\nStart: %s\nnumFound: %s\n' % \
				 (self.status, self.QTime, self.start, self.numFound)
			print json.dumps(self.docs, indent=5)

		return self.docs
	



    
