#!/usr/bin/env python3
from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('propply_report.html')

@app.route('/test')
def test():
    return "Flask is working!"

if __name__ == '__main__':
    print(f"Current directory: {os.getcwd()}")
    print(f"Templates folder exists: {os.path.exists('templates')}")
    print(f"Template file exists: {os.path.exists('templates/propply_report.html')}")
    app.run(debug=True, host='0.0.0.0', port=5000)