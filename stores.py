import collections
import logging
import logging.handlers
import urlparse
import redis
import os
from flask import jsonify

class InMemoryStore(object):

    def __init__(self, url):
        qa = urlparse.parse_qs(url.query)
        max_length = int(qa.get('max_length', ['100'])[0])

        print 'Configuring in-memory store with {settings}'.format(settings={"max_length": max_length})
        self.events = collections.deque(maxlen=max_length)

    def save(self, event):
        print event
     	print 'saving event..... \n\n'
        self.events.append(event)
    	#Save to Redis
    	#print 'opening connection to redis \n'
    	#print 'checking deployment count \n'
        #val= os.popen("curl -s localhost:5000/events 2>/dev/null | jq '.events[] | select (.eventType == \"deployment_success\") | .eventType' | wc -l").read()
        #cmdStr = "echo " + str(jsonResponse) + " | jq '.events[] | select (.eventType == \"deployment_success\") | .eventType' | wc -l"
    	#val = os.popen(cmdStr).read()
    	#print 'val : ' + val
    	#val1 = val.strip()
    	#os.close()
        #print "Connecting to Redis..."
    	#r = redis.StrictRedis(host='192.168.99.100', port=6379, db=0)
     	#r.set("app-deployment-counter", int(val))	
    	#print 'saving to redis \n'
     	#r.set("app-deployment-counter", val1)	
    	#print '\nsaved to redis\n'


    def list(self):
        return list(self.events)


class SyslogUdpStore(object):

    def __init__(self, url):
        server = url.hostname
        port = url.port or logging.handlers.SYSLOG_UDP_PORT
        address = (server, port)

        print 'Configuring syslog-udp store with {settings}'.format(settings={"server": server, "port": port})

        self.log = logging.getLogger('marathon-logger')
        facility = logging.handlers.SysLogHandler.LOG_USER
        h = logging.handlers.SysLogHandler(address, facility)
        f = logging.Formatter('marathon-logger: %(message)s')
        h.setFormatter(f)
        self.log.addHandler(h)
        self.log.setLevel(logging.getLevelName('INFO'))

    def save(self, event):
        self.log.info(event)

    def list(self):
        return []



if __name__ == '__main__':
	event_store = InMemoryStore('http://localhost/events')
	event_store.save(None)



