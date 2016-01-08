# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import requests
import nbformat
import json
import time
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

URL_TO_MESOS_DEPLOYER_API = 'https://microservices.vobpo.cloudet.xyz/api/microservices'

def _load_notebook(uri):
    '''
    Loads a local or remote notebook. Raises RuntimeError if no installed
    kernel can handle the language specified in the notebook. Otherwise,
    returns the notebook object.
    '''
    parts = urlparse(uri)

    if parts.netloc == '' or parts.netloc == 'file':
        # Local file
        with open(parts.path) as nb_fh:
            notebook = nbformat.read(nb_fh, 4)
    else:
        # Remote file
        resp = requests.get(uri)
        resp.raise_for_status()
        notebook = nbformat.reads(resp.text, 4)
    return notebook

def bundle(handler, abs_nb_path):
    notebook = _load_notebook(abs_nb_path)
    num_instances = 5
    data = {"notebook":notebook, "count":num_instances, "image":"cloudet/notebook-microservice:0.0.1"}
    data = json.dumps(data)
    headers={"Content-Type":"application/json", "X-CLOUDET-RAAM-SSO-Token":"noidea"}
    resp = requests.post(URL_TO_MESOS_DEPLOYER_API, verify=False, headers=headers, data=data)
    service_data = resp.json()
    for i in range(100):
        url_to_application_api = URL_TO_MESOS_DEPLOYER_API + '/' + service_data['id']
        resp = requests.get(url_to_application_api, verify=False, headers=headers)
        if resp.status_code == 404:
            time.sleep(1)
            continue
        data = resp.json()
        if data['count'] == num_instances:
            break
        else:
            time.sleep(1)
    handler.set_header('Content-Type', 'application/json')
    handler.finish(json.dumps({"application_id":service_data['id'], "num_instances":data['count']}))