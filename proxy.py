import boto3
import botocore
from flask import render_template, current_app, request
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
import imghdr
import os
import string
import random
from werkzeug.utils import secure_filename
from wtforms.validators import ValidationError, Regexp
from wtforms import StringField

import mysql.connector as mariadb
from datetime import datetime
import calendar
import re
from slugify import slugify

##
# Mime typing checking, taken straight from Perma (more rigorous than WTForms)
##

# Map allowed file extensions to mime types.
# WARNING: If you change this, also change `accept=""` and the label in
# uploader.html
file_extension_lookup = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif'
}

# Map allowed mime types to new file extensions and validation functions.
# We manually pick the new extension instead of using MimeTypes().guess_extension,
# because that varies between systems.
mime_type_lookup = {
    'image/jpeg': {
        'new_extension': 'jpg',
        'valid_file': lambda f: imghdr.what(f) == 'jpeg',
    },
    'image/png': {
        'new_extension': 'png',
        'valid_file': lambda f: imghdr.what(f) == 'png',
    },
    'image/gif': {
        'new_extension': 'gif',
        'valid_file': lambda f: imghdr.what(f) == 'gif',
    }
}

def get_mime_type(file_name):
    """ Return mime type (for a valid file extension) or None if file extension is unknown. """
    file_extension = file_name.rsplit('.', 1)[-1].lower()
    return file_extension_lookup.get(file_extension)

def get_filename(file_name):
    """ Return original file name without the extension. """
    file_name = file_name.rsplit('.', 1)[-2]
    return file_name

def get_extenstion(file_name):
    file_extension = file_name.rsplit('.', 1)[-1].lower()
    return file_extension

def filename_already_used(filename):
    """Technique from https://stackoverflow.com/a/33843019"""
    s3 = boto3.resource('s3',
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
    )
    exists = False
    try:
        s3.Object(current_app.config['S3_BUCKET'], filename).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            exists = False
        else:
            raise
    else:
        exists = True
    return exists

#
# WTForms custom validators
#
def valid_mimetype(form, field):
    mime_type = get_mime_type(field.data.filename)
    if not mime_type or not mime_type_lookup[mime_type]['valid_file'](field.data):
        raise ValidationError("Invalid file format")

class UploadForm(FlaskForm):
    file = FileField(validators=[FileRequired(), valid_mimetype],
                     label="valid formats: {}".format(", ".join(file_extension_lookup.keys())))
    title = StringField(label="Your Title")

def proxy_request(request, path):
    '''
        This function will be called on every web request caught by our
        default route handler (that is, on every request except for:
        a) requests for resources in /static and
        b) requests for urls with route especially defined in app.py.

        request = the request object as received by the parent Flask
        view function (http://flask.pocoo.org/docs/0.12/api/#incoming-request-data)

        path = the route requested by the user (e.g. '/path/to/route/i/want')

        proxy_response should return the response to be forwarded to the user.
        Treat it like a normal Flask view function:

        It should return a value that Flask can convert into a response using
        http://flask.pocoo.org/docs/0.12/api/#flask.Flask.make_response,
        just like any function you woulld normally decorate with @app.route('/route'),
        where Flask calls make_response implicitly.

        e.g.
        def proxy_request(request, path):
            return 'Hello World'

        You can use flask.make_response to help construct complex responses:
        http://flask.pocoo.org/docs/0.12/api/#flask.Flask.make_response
    '''
    form = UploadForm()
    if form.validate_on_submit():
        # Get a safe filename
        f = form.file.data
        filename = secure_filename(f.filename)
        unique_filename = False
        while not unique_filename:
            if filename_already_used(filename):
                fn, ext = os.path.splitext(filename)
                filename = '{}-{}{}'.format(fn, ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(3)), ext)
                continue
            unique_filename = True

        # Get file format
        image_format = get_mime_type(filename)

        # Extract original file name (w/o file extension)
        original_name = get_filename(filename)

        # Get user's title for the file
        title = request.form['title']
        if title == '':
            image_title = original_name
        else:
            image_title = title

        # Get datetime of submission
        now = datetime.now()
        image_datetime = now.strftime('%Y-%m-%d %H:%M:%S')

        # Create a unique identifier for every image
        ## Get a timestamp

        timestamp = str(calendar.timegm(now.utctimetuple()))
        file_extension = get_extenstion(filename)
        new_filename = '-'.join([timestamp, slugify(image_title, separator="_")])
        image_id = '.'.join([new_filename, file_extension])

        # Upload to MariaDB
        mariadb_connection = mariadb.connect(host=current_app.config['HOST'], user=current_app.config['USER'], password=current_app.config['PASSWORD'], database=current_app.config['DB'])

        cursor = mariadb_connection.cursor()

        try:
            cursor.execute("INSERT INTO images (_id,date,format,original_filename,given_title) VALUES (%s,%s,%s,%s,%s)", (image_id,image_datetime,image_format,original_name,image_title))
        except mariadb.Error as error:
            print "Error: {}".format(error)

        mariadb_connection.commit()
        print 'File inserted successfully!'

        mariadb_connection.close()

        # Upload to s3
        s3 = boto3.client(
            's3',
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        )

        s3.upload_fileobj(f.stream, 'archive-my-trash', image_id, ExtraArgs={'ContentType': get_mime_type(filename)})

        return render_template('success.html', context={'heading': "Your file is up!" ,
                                                        'url': "https://{}.s3.amazonaws.com/{}".format(current_app.config['S3_BUCKET'], filename) })
    return render_template('uploader.html', context={'heading': 'Trash Exchange', 'limit': current_app.config['MAX_CONTENT_LENGTH']/1024/1024}, form=form)

