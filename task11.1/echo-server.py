import json
import logging
import redis

from flask import Flask, request
from pymongo import MongoClient

app = Flask(__name__)

from logging.config import fileConfig
fileConfig('logging.conf')
app.logger = logging.getLogger()

OK = 'Ok', 200
CREATED = 'Created', 201
NOT_FOUND = 'Not Found', 404
ALREADY_EXISTS = 'Already Exists', 409

HOST = '0.0.0.0'
PORT = 4567
CACHE_HOST = 'cache'
CACHE_PORT = 6379
DB_HOST = 'mongo'
DB_PORT = 27017

class Cache:
    def __init__(self, host=CACHE_HOST, port=CACHE_PORT):
        self.cache = redis.Redis(host=host, port=port)
        self.cache.ping()

    def exists(self, key):
        return self.cache.exists(key)

    def post(self, key, message):
        app.logger.debug('post for key [%s]', key)
        if not self.exists(key):
            self.cache.set(key, json.dumps(message))
            return True
        return False

    def put(self, key, message):
        app.logger.debug('put for key [%s]', key)
        if self.exists(key):
            self.cache.set(key, json.dumps(message))
            return True
        return False

    def get(self, key):
        app.logger.debug('get for key [%s]', key)
        if self.exists(key):
            return json.loads(self.cache.get(key))
        return None

    def delete(self, key):
        app.logger.debug('delete for key [%s]', key)
        if self.exists(key):
            self.cache.delete(key)


class Database:
    def __init__(self, host=DB_HOST, port=DB_PORT):
        client = MongoClient(host, port)
        db = client['test-database']
        self.storage = db['test-collection']

    def exists(self, key):
        return self.storage.find_one({"key": key}) is not None

    def post(self, key, message):
        app.logger.debug('post for key [%s]', key)
        if not self.exists(key):
            self.storage.insert_one({"key": key, "message": message})
            return True
        return False

    def put(self, key, message):
        app.logger.debug('put for key [%s]', key)
        data = self.storage.find_one({"key": key})
        if data:
            self.storage.update_one(data, {'$set': {"key": key, "message": message}})
            return True
        return False

    def get(self, key):
        app.logger.debug('get for key [%s]', key)
        data = self.storage.find_one({"key": key})
        if data:
            return data["message"]
        return None

    def delete(self, key):
        app.logger.debug('delete for key [%s]', key)
        if self.exists(key):
            self.storage.delete_one({"key": key})


class Storage:
    def __init__(self):
        self.cache = Cache()
        self.db = Database()

    def post(self, key, message):
        return self.db.post(key, message)

    def put(self, key, message):
        return self.db.put(key, message)

    def get(self, key):
        if self.cache.exists(key):
            return self.cache.get(key)
        app.logger.warning('no data in cache for key [%s]', key)
        data = self.db.get(key)
        if data:
            self.cache.put(key, data)
        else:
            app.logger.error('no data in database for key [%s]', key)
        return data

    def delete(self, key):
        self.cache.delete(key)
        self.db.delete(key)


@app.route("/<key>", methods=['POST', 'PUT', 'GET', 'DELETE'])
def listener(key):
    app.logger.info('%s', request)
    storage = Storage()
    try:
        if request.method == 'POST':
            message = json.loads(request.data)
            status = storage.post(key, message)
            if status:
                return CREATED
            return ALREADY_EXISTS

        elif request.method == 'PUT':
            message = json.loads(request.data)
            status = storage.put(key, message)
            if status:
                return OK
            return NOT_FOUND

        elif request.method == 'GET':
            message = storage.get(key)
            if message is None:
                return NOT_FOUND

            return app.response_class(
                response=json.dumps(message),
                status=200,
                mimetype='application/json'
            )

        elif request.method == 'DELETE':
            storage.delete(key)
            return OK

    except Exception as err:
        return "Unexpected error occurred: " + str(err), 500

if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
