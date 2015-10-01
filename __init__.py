__author__ = 'Bernard'

from flask import Flask

app = Flask(__name__)
app.config.from_object('Components.config')
