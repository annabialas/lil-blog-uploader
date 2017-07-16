from os import environ
from flask import render_template, current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from datetime import datetime
import calendar

import mysql.connector as mariadb

mariadb_connection = mariadb.connect(user=current_app.config['USER'], password=current_app.config['PASSWORd'], database=current_app.config['DB'])

cursor = mariadb_connection.cursor()

#insert object into db

now = datetime.now()

new_id = 
new_original_name = 
new_format = 
new_s3_path = 
new_datetime = now.strftime('%Y-%m-%d %H:%M:%S')

try:
    cursor.execute("INSERT INTO images (_id, original_name, format, s3_path, datetime) VALUES (%s,%s,%s,%s,%s)", (new_id, new_original_name, new_format, new_s3_path, new_datetime))
except mariadb.Error as error:
    print("Error: {}".format(error))

mariadb_connection.commit()
print "The last inserted id was: ", cursor.lastrowid

mariadb_connection.close()


