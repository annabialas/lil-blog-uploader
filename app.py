import os
from os import environ
from ast import literal_eval
import requests
from functools import wraps
from urlparse import urlparse, urljoin
from datetime import datetime, timedelta

from flask import Flask, request, redirect, session, abort, url_for, render_template
import error_handling
from proxy import proxy_request

import logging

app = Flask(__name__)

# Fighting CSS caching via http://flask.pocoo.org/snippets/40/
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

app.config['SECRET_KEY'] = environ.get('FLASK_SECRET_KEY')

# Specific to this proxy
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 ## 16MB
app.config['S3_BUCKET'] = environ.get('S3_BUCKET')
app.config['AWS_ACCESS_KEY_ID'] = environ.get('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = environ.get('AWS_SECRET_ACCESS_KEY')
app.config['USER'] = environ.get('USER')
app.config['PASSWORD'] = environ.get('PASSWORD')
app.config['DB'] = environ.get('DB')
app.config['HOST'] = environ.get('HOST')

# register error handlers
error_handling.init_app(app)

###
### ROUTES
###

# @app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])

# @app.route('/<path:path>')

@app.route('/')
def render_index():
    return render_template('index.html', context={'heading': "Trash Exchange"})

@app.route('/can', methods=['GET', 'POST'])
def provide_exchange():

    try:
        proxied_response = proxy_request(request)
        if proxied_response:
            return proxied_response
        else:
            app.logger.warning("No response returned by proxied endpoint.")
            return render_template('generic.html', context={'heading': "Trash Exchange",'message': "in the try"})
    except NameError:
        app.logger.warning("No proxy function available.")
        return render_template('generic.html', context={'heading': "Trash Exchange",'message': "no proxy"})

# def catch_all(path):
#     '''
#         All requests are caught by this route, unless explicitly caught by
#         other more specific patterns.
#         http://flask.pocoo.org/docs/0.12/design/#the-routing-system
#     '''
#     def fallback():
#         return render_template('generic.html', context={'heading': "Trash Exchange",
#                                                         'message': "a static site helper"})

#     try:
#         proxied_response = proxy_request(request, path)
#         if proxied_response:
#             return proxied_response
#         else:
#             app.logger.warning("No response returned by proxied endpoint.")
#             return fallback()
#     except NameError:
#         app.logger.warning("No proxy function available.")
#         return fallback()
