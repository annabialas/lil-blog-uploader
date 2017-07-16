# from os import environ
# from flask import render_template, current_app
# from flask_wtf import FlaskForm
# from flask_wtf.file import FileField, FileRequired

# from datetime import datetime
# import calendar

# import mysql.connector as mariadb

# mariadb_connection = mariadb.connect(user=current_app.config['USER'], password=current_app.config['PASSWORd'], database=current_app.config['DB'])

# cursor = mariadb_connection.cursor()

# try:
#     cursor.execute("INSERT INTO images (title, dt) VALUES (%s,%s)", (image_title, image_datetime))
# except mariadb.Error as error:
#     print("Error: {}".format(error))

# mariadb_connection.commit()
# print 'File inserted successfully!'
# # print "The last inserted id was: ", cursor.lastrowid

# mariadb_connection.close()


