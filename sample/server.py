import os

import elasticsearch

from flask import Flask
from flask_cors import CORS

from apies import apies_blueprint

DATAPACKAGE = 'data/datapackage.json'
ES_HOST = os.environ.get('ES_HOST', 'localhost')
ES_PORT = int(os.environ.get('ES_PORT', '9200'))
INDEX_NAME = 'jobs'

app = Flask(__name__)
CORS(app)
blueprint = apies_blueprint(
    app,
    [DATAPACKAGE],
    elasticsearch.Elasticsearch([dict(host=ES_HOST, port=ES_PORT)], timeout=60),
    'jobs',
    dont_highlight={
        'Salary Frequency',
    },
)
app.register_blueprint(blueprint, url_prefix='/search/')

if __name__ == '__main__':
    app.run()
