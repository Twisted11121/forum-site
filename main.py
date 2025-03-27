from flask import Flask, render_template, request
import sqlite3


app = Flask(__name__)
database = 'database.db'


@app.route('/')
def index():
    return render_template('index.html')
