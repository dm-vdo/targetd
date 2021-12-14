#!/usr/bin/env python3

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
    #Ensure we have version string
    assert response.get('jsonrpc') == "2.0"
    if response.get('error') is not None:
        if response['error']['code'] <= 0:
            raise Exception(response['error'].get('message', ''))
        else:
            print("Invalid error code, should be negative!")
    else:
        return response.get('result')
def parse_arguments():
  parser = argparse.ArgumentParser()
  parser.add_argument('--host', help = "The host providing the REST API/iSCSI target",
                      action = "store",
                      dest = "host",
                      default = None)
  parser.add_argument('--initiatorName', help = "List out all exports to initiatorName",
                      action = "store",
                      dest = "initiatorName",
                      default = None)
  parser.add_argument("--lun", help = "The lun number to export",
                      action = "store",
                      dest = "lunNum",
                      default = None)
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
  # Right now, only accept bytes, but add support for units later.  For now, if
  # you want GB, then specify the argument as $((1024*1024*1024 *
  # <size_in_GB>))
  parser.add_argument('--size', help = "The size of the LUN to create (in bytes)",
                      action = "store",
                      dest = "volSize",
                      default = None)
  args = parser.parse_args()


  errors = []
  # We can't continue without a volume size or name
  if args.host is None:
    errors.append("Target host is required (specify with --host)")
  if args.lunNum is None:
    errors.append("LUN number is required (specify with --lun)")
  if args.pool is None:
    errors.append("Pool name is required (specify with --pool)")
  if (args.volSize is None) or (int(args.volSize) <= 0):
    errors.append("Volume Size is required and greater than 0")
  if args.volName is None:
    errors.append("Volume Name is required")


  if len(errors) > 0:
    print("Errors found:")
    for error in errors:
      print("  %s" % error)
    print()
    parser.print_usage()

    sys.exit(1)
  return args

if __name__ == "__main__":
  args = parse_arguments()

  # Temporarily assign older variable names to the args results for now.
  host = args.host
  initiatorName = args.initiatorName
  lunNum = args.lunNum
  password = args.password
  pool = args.pool
  port = args.port
  user = args.user
  volName = args.volName
  volSize = args.volSize

  # Configurables that really don't need to change
  id_num = 1
  path = '/targetrpc'
  ssl = False

  if initiatorName is None:
    # Load the initiator name from the /etc/iscsi/initiatorname.iscsi, since this
    # is what will be used for iscsiadm calls.
    if not os.path.isfile('/etc/iscsi/initiatorname.iscsi'):
      print("/etc/iscsi/initiatorname.iscsi is missing, is iscsi-initiator-utils installed?")
      sys.exit(1)
    with open('/etc/iscsi/initiatorname.iscsi', 'r') as initfile:
      for line in initfile:
        match = re.search('^InitiatorName=(.*)$', line)
        if match:
          initiatorName = match.group(1)
          break

  try:
    jsonrequest('vol_create', dict(pool=pool, name=volName, size=volSize))
    try:
      jsonrequest('export_create', dict(pool=pool,
                                        vol=volName,
                                        lun=lunNum,
                                        initiator_wwn=initiatorName))
    except Exception as export_error:
      print("Problem creating export: %s" % export_error)
      jsonrequest("export_destroy", dict(pool=pool, name=volName, initiator_wwn=initiatorName))

  except Exception as create_error:
    print("Problem executing vol_create: %s" % create_error)
    jsonrequest("vol_destroy", dict(pool=pool, name=volName))

  print("Created Volume - Pool:%s - Name:%s - Size:%s - Initiator:%s - LUN:%s" % (pool, volName, volSize, initiatorName, lunNum))

  sys.exit(0)
