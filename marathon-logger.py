#!/usr/bin/env python

import argparse
import atexit
import sys
import urlparse

from flask import Flask, request, jsonify
import marathon

from stores import InMemoryStore, SyslogUdpStore, ElasticSearchStore

import json

import logging

log = logging.getLogger('werkzeug')
log.disabled = True


app = Flask(__name__)

# re-initialize later
events = None
event_store = None

def on_exit(marathon_client, callback_url):
    marathon_client.delete_event_subscription(callback_url)

@app.route('/events', methods=['POST'])
def event_receiver():
    #print event
    event = request.get_json()
    event_store.save(event)
    
    print json.dumps(event)
    return ''

@app.route('/events', methods=['GET'])
def list_events():
    #print jsonify({'events': event_store.list()})
    return jsonify({'events': event_store.list()})


@app.route('/restart-events', methods=['GET'])
def list_restart_events():
    all_event_list = event_store.list()
    print 'event length : ' + str(len(all_event_list))
    all_events = jsonify({'events': all_event_list})
    # print 'all_events ' + str(all_event_list)
    print 'parsing the json ..... '
    parsed_json = json.loads("{'hello': 'world'}")
    #print parsed_json["hello"]
    # print event_store.list()
    return "hello"



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Marathon Logging Service')
    parser.add_argument('-m', '--marathon-url', required=True, help='Marathon server URL (http[s]://<host>:<port>[<path>])')
    parser.add_argument('-c', '--callback-url', required=True, help='callback URL for this service (http[s]://<host>:<port>[<path>]/events')
    parser.add_argument('-e', '--event-store', default='in-memory://localhost/', help='event store connection string (default: in-memory://localhost/)')
    parser.add_argument('-p', '--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    parser.add_argument('-i', '--ip', default='0.0.0.0', help='IP to listen on (default: 0.0.0.0)')
    args = parser.parse_args()

    event_store_url = urlparse.urlparse(args.event_store)

    if event_store_url.scheme == 'in-memory':
        event_store = InMemoryStore(event_store_url)
    elif event_store_url.scheme == 'syslog':
        event_store = SyslogUdpStore(event_store_url)
    elif event_store_url.scheme == "elasticsearch":
        event_store = ElasticSearchStore(event_store_url)
    else:
        print 'Invalid event store type: "{scheme}" (from "{url}")'.format(scheme=event_store_url.scheme, url=args.event_store)
        sys.exit(1)

    m = marathon.MarathonClient(args.marathon_url)
    m.create_event_subscription(args.callback_url)
    atexit.register(on_exit, m, args.callback_url)

    app.run(port=args.port, host=args.ip)

