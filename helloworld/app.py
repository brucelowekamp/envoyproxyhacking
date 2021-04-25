#!/usr/bin/python

import os
import math
from flask import Flask, request
app = Flask(__name__)


@app.route('/hello')
def hello():
    return 'Hello from instance: %s\n' % (os.environ.get('HOSTNAME'))

@app.route('/health')
def health():
    return 'Helloworld is healthy', 200

@app.route('/')
def root():
    msg = 'instance: %s user: %s tenant: %s' % (os.environ.get('HOSTNAME'),
                                                request.headers.get('x-user'),
                                                request.headers.get('x-tenant'))
    

    return msg
    


if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=True)
