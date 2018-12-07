import logging

from flask import Blueprint, request, app
from flask_jsonpify import jsonpify
from flask.helpers import NotFound

import demjson

from .controllers import search, count, timeline, get_document
from .sources import extract_text_fields

DEFAULT_RULES = dict([
    # es:title, es:keyword -> suffixes (by default: [''])
    ((True,     False),       ['^3', '.hebrew^10']),
    ((True,     True),        ['^10']),
])


def search_handler(types, search_term, from_date, to_date, size, offset):
    es_client = app.config['ES_CLIENT']
    index_name = app.config['INDEX_NAME']
    text_fields = app.config['TEXT_FIELDS']
    dont_highlight = app.config['DONT_HIGHLIGHT']

    try:
        types_formatted = str(types).split(',')
        filters = request.values.get('filter')
        result = search(es_client, index_name, text_fields,
                        types_formatted, search_term, 
                        from_date, to_date, 
                        size, offset, filters, dont_highlight)
    except Exception as e:
        logging.exception('Error searching %s for types: %s ' % (search_term, str(types)))
        result = {'error': str(e)}
    return jsonpify(result)


def simple_search_handler(types, search_term):
    es_client = app.config['ES_CLIENT']
    index_name = app.config['INDEX_NAME']
    text_fields = app.config['TEXT_FIELDS']

    try:
        types_formatted = str(types).split(',')
        filters = request.values.get('filter')
        result = search(es_client, index_name, text_fields,
                        types_formatted, search_term, 
                        None, None, 100, 0, filters)
    except Exception as e:
        logging.exception('Error searching %s for tables: %s ' % (search_term, str(types)))
        result = {'error': str(e)}
    return jsonpify(result)


def count_handler(search_term, from_date, to_date):
    es_client = app.config['ES_CLIENT']
    index_name = app.config['INDEX_NAME']
    text_fields = app.config['TEXT_FIELDS']

    config = request.values.get('config')
    try:
        config = demjson.decode(config)
        result = count(es_client, index_name, text_fields,
                       search_term, 
                       from_date, to_date, config)
    except Exception as e:
        logging.exception('Error counting with config %r', config)
        result = {'error': str(e)}
    return jsonpify(result)


def simple_count_handler(search_term):
    es_client = app.config['ES_CLIENT']
    index_name = app.config['INDEX_NAME']
    text_fields = app.config['TEXT_FIELDS']

    config = request.values.get('config')
    try:
        config = demjson.decode(config)
        result = count(es_client, index_name, text_fields,
                       search_term, None, None, config)
    except Exception as e:
        logging.exception('Error counting with config %r', config)
        result = {'error': str(e)}
    return jsonpify(result)


def timeline_handler(types, search_term, from_date, to_date):
    es_client = app.config['ES_CLIENT']
    index_name = app.config['INDEX_NAME']
    text_fields = app.config['TEXT_FIELDS']

    try:
        types_formatted = str(types).split(',')
        filters = request.values.get('filter')
        result = timeline(es_client, index_name, text_fields,
                          types_formatted, search_term, 
                          from_date, to_date, filters)
    except Exception as e:
        logging.exception('Error getting timeline %s for types: %s ' % (search_term, str(types)))
        result = {'error': str(e)}
    return jsonpify(result)


def get_document_handler(doc_id):
    es_client = app.config['ES_CLIENT']
    index_name = app.config['INDEX_NAME']
    doctype = app.config['DOCUMENT_DOCTYPE']

    result = get_document(es_client, index_name, 
                          doctype, doc_id)
    if result is None:
        logging.warning('Failed to fetch document for %r', doc_id)
        raise NotFound()
    return jsonpify(result)


def make_blueprint(sources,
                   es_client, 
                   index_name, 
                   document_doctype='document',
                   dont_highlight=[],
                   text_field_rules=DEFAULT_RULES):
    blueprint = Blueprint()

    blueprint.add_url_rule(
        '/search/<string:types>/<string:search_term>/'
           '<string:from_date>/<string:to_date>/'
           '<string:size>/<string:offset>',
        search_handler,
        methods=['GET']
    )
    blueprint.add_url_rule(
        '/search/<string:types>/<string:search_term>',
        simple_search_handler,
        methods=['GET']
    )
    blueprint.add_url_rule(
        '/search/count/<string:search_term>/'
           '<string:from_date>/<string:to_date>',
        count_handler,
        methods=['GET']
    )
    blueprint.add_url_rule(
        '/search/count/<string:search_term>',
        simple_count_handler,
        methods=['GET']
    )
    blueprint.add_url_rule(
        '/search/timeline/<string:types>/<string:search_term>/'
           '<string:from_date>/<string:to_date>',
        timeline_handler,
        methods=['GET']
    )
    blueprint.add_url_rule(
        '/get/<path:doc_id>',
        get_document_handler,
        methods=['GET']
    )

    app.config['TEXT_FIELDS'] = extract_text_fields(sources, text_field_rules)
    app.config['ES_CLIENT'] = es_client
    app.config['INDEX_NAME'] = index_name
    app.config['DOCUMENT_DOCTYPE'] = document_doctype
    app.config['DONT_HIGHLIGHT'] = dont_highlight

    return blueprint

    