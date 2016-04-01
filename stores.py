import collections
import logging
import logging.handlers
import urlparse
from elasticsearch import Elasticsearch
import datetime
import requests
import json



class CustomEndPointStore(object):
    
    custom_store = None
    index = None
    current_id = 1 # Used for elasticsearch _id 
    index_type = None
    old_deploy_ids = []
    log = logging.getLogger('werkzeug')
    log_type = None

    def __init__(self, url):

        server = str(url.hostname)
        port = str(url.port)        
        self.log.info('Configuring custom store with ' + server + ":" + port)
        self.host = server
        self.port = port
        
        self.index = "my-index"
        self.index_type = "marathon"
        self.log_type = "marathon"

        self.log = logging.getLogger('marathon-logger')
        facility = logging.handlers.SysLogHandler.LOG_USER
        f = logging.Formatter('marathon-logger: %(message)s')
       
        self.log.setLevel(logging.getLevelName('INFO'))

        return None       

    def save(self, event):
        try:
            self.current_id = self.current_id + 1
            if 'appId' in event:
                #self.es.index(index= self.index, doc_type=self.index_type, id=self.current_id, body={"log_type": "marathon", "log_id": self.current_id, "event_type" : event["eventType"], "timestamp": event["timestamp"], "app_id": event["appId"]})
                print "no relevant info for Custom Store"

            elif 'plan' in event:
                length = len(event["plan"]["target"]["groups"]) # Total number of app groups in the target state
                size_original_groups = len(event["plan"]["original"]["groups"]) # Total number of app groups in the original state
                
                if length > size_original_groups:
                    new_group_id = size_original_groups
                else:
                    new_group_id = size_original_groups - 1
                
                labels = event["plan"]["target"]["groups"][new_group_id]["groups"][0]["apps"][0]["labels"]

                if "ENV" not in labels:
                    return

                environment = labels["ENV"] 
                print 'env : ' + str(environment)
                
                eventType = event["eventType"]
                timestamp = event["timestamp"]
                app_id = event["plan"]["id"]
                project_name = event["plan"]["target"]["groups"][new_group_id]["groups"][0]["apps"][0]["labels"]["PROJECT"]
                deploy_id = event["plan"]["target"]["groups"][new_group_id]["groups"][0]["apps"][0]["labels"]["DEPLOYID"]

                #self.es.index(index= self.index, doc_type=self.index_type, body={"log_type": self.log_type,  "event_type" : eventType, "timestamp": timestamp, "marathon_deploy_id": app_id, "application": project_name, "deploy_id": deploy_id, "environment": environment})

                request_query_data  = {"environment": environment, "application": project_name, "event_type": eventType, "timestamp": timestamp, "deploy_id":deploy_id, "log_type": self.log_type, "marathon_deploy_id": app_id}
                custom_store_full_url = "http://"+self.host+":"+self.port+"/api/marathon/avg_time?event_log="+str(json.dumps(request_query_data))
                print 'custom_store_full_url ' + str(custom_store_full_url)

                r = requests.get(custom_store_full_url)
                data = json.loads(r.content)
                print data

                self.current_id = self.current_id + 1
                print "Sent to CustomStore !"
        except Exception as inst:
            print "Exception happened !"
            print inst

        

    def list(self):
        #return list(self.events)
        return None


class ElasticSearchStore(object):

    es = None
    index = None
    current_id = 1 # Used for elasticsearch _id 
    index_type = None
    old_deploy_ids = []
    log = logging.getLogger('werkzeug')
    log_type = None

    def __init__(self, url):

        server = str(url.hostname)
        port = str(url.port)        
        self.log.info('Configuring elasticsearch store with ' + server + ":" + port)
        self.es = Elasticsearch([{'host': server, 'port': port, 'use_ssl': False}])
        
        self.index = "my-index"
        self.index_type = "marathon"
        self.log_type = "marathon"


        self.log = logging.getLogger('marathon-logger')
        facility = logging.handlers.SysLogHandler.LOG_USER
        f = logging.Formatter('marathon-logger: %(message)s')
       
        self.log.setLevel(logging.getLevelName('INFO'))

        return None

    def save(self, event):
        try:
            self.current_id = self.current_id + 1
            if 'appId' in event:
                self.es.index(index= self.index, doc_type=self.index_type, id=self.current_id, body={"log_type": "marathon", "log_id": self.current_id, "event_type" : event["eventType"], "timestamp": event["timestamp"], "app_id": event["appId"]})
            elif 'plan' in event:
                length = len(event["plan"]["target"]["groups"]) # Total number of app groups in the target state
                size_original_groups = len(event["plan"]["original"]["groups"]) # Total number of app groups in the original state
                
                if length > size_original_groups:
                    new_group_id = size_original_groups
                else:
                    new_group_id = size_original_groups - 1
                
                labels = event["plan"]["target"]["groups"][new_group_id]["groups"][0]["apps"][0]["labels"]

                if "ENV" not in labels:
                    return

                environment = labels["ENV"] 
                print 'env : ' + str(environment)
                
                eventType = event["eventType"]
                timestamp = event["timestamp"]
                app_id = event["plan"]["id"]
                project_name = event["plan"]["target"]["groups"][new_group_id]["groups"][0]["apps"][0]["labels"]["PROJECT"]
                deploy_id = event["plan"]["target"]["groups"][new_group_id]["groups"][0]["apps"][0]["labels"]["DEPLOYID"]

                self.es.index(index= self.index, doc_type=self.index_type, body={"log_type": self.log_type,  "event_type" : eventType, "timestamp": timestamp, "marathon_deploy_id": app_id, "application": project_name, "deploy_id": deploy_id, "environment": environment})
                self.current_id = self.current_id + 1
        except Exception as inst:
            print "Exception happened !"
            print inst

        print "Sent to ElasticSearchStore !"

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
