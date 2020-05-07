#!/usr/bin/env python

# based on code from git://github.com/openstack/nova.git
# nova/volume/nexenta/jsonrpc.py
#
# Copyright 2011 Nexenta Systems, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2012, Andy Grover <agrover@redhat.com>
#
# Test client to exercise targetd.
#

import argparse
import base64
import json
import os
import re
import socket
import sys
import time

try:
    from urllib.request import (Request,
                                urlopen)
except ImportError:
    from urllib2 import (Request,
                         urlopen)

def jsonrequest(method, params=None):
    global id_num
    data = json.dumps(
        dict(id=id_num, method=method, params=params, jsonrpc="2.0"))
    id_num += 1
    username_pass = '%s:%s' % (user, password)
    auth = base64.b64encode(username_pass.encode('utf-8')).decode('utf-8')
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Basic %s' % (auth,)}

    if ssl:
        scheme = 'https'
    else:
        scheme = 'http'

    url = "%s://%s:%s%s" % (scheme, host, port, path)
    try:
        request = Request(url, data.encode('utf-8'), headers)
        response_obj = urlopen(request)
    except socket.error as e:
        print("error, retrying with SSL")
        url = "https://%s:%s%s" % (host, port, path)
        request = Request(url, data, headers)
        response_obj = urlopen(request)

    response_data = response_obj.read().decode('utf-8')

    response = json.loads(response_data)
    # print('Got response: %s' % response_data)
    #Ensure we have version string
    assert response.get('jsonrpc') == "2.0"
    if response.get('error') is not None:
        if response['error']['code'] <= 0:
            raise Exception(response['error'].get('message', ''))
        else:
            print("Invalid error code, should be negative!")
    else:
        return response.get('result')

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--client', help = "The client to allow mounts from",
                      action = "store",
                      dest = "client",
                      default = "*")
  parser.add_argument('--host', help = "The host providing the REST API/iSCSI target",
                      action = "store",
                      dest = "host",
                      default = '192.168.121.247')
  parser.add_argument('--password', help = "Authentication with REST API: Password",
                      action = "store",
                      dest = "password",
                      default = "password")
  parser.add_argument('--pool', help = "The pool to create the LUN from",
                      action = "store",
                      dest = "pool",
                      default = None)
  parser.add_argument('--port', help = "The port for the REST API",
                      action = "store",
                      dest = "port",
                      default = 18700)
  parser.add_argument('--user', help = "Authentication with REST API: Username",
                      action = "store",
                      dest = "user",
                      default="admin")
  parser.add_argument('--name', help = "The name of the volume to create",
                      action = "store",
                      dest = "volName",
                      default = None)
  args = parser.parse_args()

  # Temporarily assign older variable names to the args results for now.
  client = args.client
  host = args.host
  password = args.password
  pool = args.pool
  port = args.port
  user = args.user
  volName = args.volName

  errors = []
  if volName is None:
    errors.append("A volume name is required")
    parser.print_usage()
  if pool is None:
    errors.append("A pool is required")
    parser.print_usage()

  if len(errors) > 0:
    for error in errors:
      print "Error: %s" % error
    sys.exit(1)

  # Configurables that really don't need to change
  id_num = 1
  path = '/targetrpc'
  ssl = False

  #XXX: Add a try catch here.
  results = jsonrequest("nfs_export_remove", dict(client=client, pool=pool, name=volName))
  sys.exit(0)
