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

app.config['SECRET_KEY'] = environ.get('FLASK_SECRET_KEY')

# Specific to this proxy
app.config['MAX_CONTENT_LENGTH'] = environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024) ## 16MB
app.config['S3_BUCKET'] = environ.get('S3_BUCKET')
app.config['AWS_ACCESS_KEY_ID'] = environ.get('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = environ.get('AWS_SECRET_ACCESS_KEY')

# register error handlers
error_handling.init_app(app)

###
### ROUTES
###

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>')
def catch_all(path):
    '''
        All requests are caught by this route, unless explicitly caught by
        other more specific patterns.
        http://flask.pocoo.org/docs/0.12/design/#the-routing-system
    '''
    def fallback():
        return render_template('generic.html', context={'heading': "lil blog media uploader",
                                                        'message': "a static site helper"})

    try:
        proxied_response = proxy_request(request, path)
        if proxied_response:
            return proxied_response
        else:
            app.logger.warning("No response returned by proxied endpoint.")
            return fallback()
    except NameError:
        app.logger.warning("No proxy function available.")
        return fallback()
