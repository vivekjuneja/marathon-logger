import collections
import logging
import logging.handlers
import urlparse
from elasticsearch import Elasticsearch
import datetime



class ElasticSearchStore(object):

    es = None
    current_id = 1

    def __init__(self, url):

        print 'url : ' + str(url) 
        print 'Configuring elasticsearch store with ' + str(url)
        self.es = Elasticsearch([{'host': '10.52.32.59', 'port': '9200', 'use_ssl': False}])
        print self.es

        return None

    def save(self, event):
        print "Save Event to ElasticSearchStore"
        #print "event : " + str(event)

        try:
            self.current_id = self.current_id + 1
            if 'appId' in event:
                self.es.index(index="my-index", doc_type="marathon", id=self.current_id, body={"eventType" : event["eventType"], "timestamp": event["timestamp"], "appId": event["appId"]})
            elif 'plan' in event:
                length = len(event["plan"]["target"]["groups"])
                print 'length : ' + str(length)
                for i in range(0,length):
                    print "ENV : " + str(event["plan"]["target"]["groups"][i]["groups"][0]["apps"][0]["labels"]["ENV"])
                    self.es.index(index="my-index", doc_type="marathon", id=self.current_id, body={"eventType" : event["eventType"], "timestamp": event["timestamp"], "ID": event["plan"]["id"], "application": event["plan"]["target"]["groups"][i]["groups"][0]["apps"][0]["labels"]["JOB_NAME"], "deploy_id": event["plan"]["target"]["groups"][i]["groups"][0]["apps"][0]["labels"]["DEPLOYID"], "environment": event["plan"]["target"]["groups"][i]["groups"][0]["apps"][0]["labels"]["ENV"] })
                    self.current_id = self.current_id + 1
        except Exception as inst:
            print "Exception happened !"
            print inst

        print "Save Done !"

    def list(self):
        #return list(self.events)
        return None




class InMemoryStore(object):

    def __init__(self, url):
        qa = urlparse.parse_qs(url.query)
        max_length = int(qa.get('max_length', ['100'])[0])

        #print 'Configuring in-memory store with {settings}'.format(settings={"max_length": max_length})

        self.events = collections.deque(maxlen=max_length)

    def save(self, event):
        #print event
        self.events.append(event)

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
