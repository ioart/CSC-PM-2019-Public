#!/usr/bin/env python
#coding=utf-8
import json
import requests
import pytest

HOST = '0.0.0.0'
PORT = '5000'

def send_request(sessions):
    for method, key, message, status in sessions:
        address = 'http://' + HOST + ':' + PORT + '/' + key
        if method == 'POST':
            response = requests.post(address, json=message)
        if method == 'PUT':
            response = requests.put(address, json=message)
        elif method == 'GET':
            response = requests.get(address)
        elif method == 'DELETE':
            response = requests.delete(address)

        request_str = '{method} {address}'.format(method=method, address=address)
        if message:
            request_str += ' "{}"'.format(message)

        data = response.text
        if 'application/json' in response.headers['Content-Type']:
            data = json.loads(data)

        assert data == status, "request: {}".format(request_str)

def test_empty_message():
    sessions = [
        # method, key, message, --  status
        ['POST',   '1', '""', 'Created'],
        ['POST',   '1', '""', 'Already Exists'],
        ['GET',    '1', None, '""'],
        ['DELETE', '1', None, 'Ok'],
        ['GET',    '1', None, 'Not Found'],
        ['DELETE', '1', None, 'Ok'],
    ]
    send_request(sessions)

def test_diff_keys():
    sessions = [
        # method, key, message, --  status
        ['POST',   '3', 'this is a key 3', 'Created'],
        ['POST',   '4', 'this is a key 4', 'Created'],
        ['DELETE', '3', None, 'Ok'],
        ['GET',    '3', None, 'Not Found'],
        ['GET',    '4', None, 'this is a key 4'],
        ['DELETE', '4', None, 'Ok'],
    ]
    send_request(sessions)

def test_override():
    sessions = [
        # method, key, message, --  status
        ['POST',   '6', 'key 6', 'Created'],
        ['POST',   '6', 'key 7', 'Already Exists'],
        ['GET',    '6', None, 'key 6'],
        ['PUT',    '6', 'key 8', 'Ok'],
        ['GET',    '6', None, 'key 8'],
        ['DELETE', '6', None, 'Ok'],
    ]
    send_request(sessions)

def test_numeric_message():
    sessions = [
        # method, key, message, --  status
        ['POST',   '7', 125, 'Created'],
        ['GET',    '7', None, 125],
        ['DELETE', '7', None, 'Ok'],
    ]
    send_request(sessions)

def test_list_message():
    sessions = [
        # method, key, message, --  status
        ['POST',   '8', [2, 4], 'Created'],
        ['GET',    '8', None, [2, 4]],
        ['DELETE', '8', None, 'Ok'],
    ]
    send_request(sessions)

def test_dict_message():
    sessions = [
        # method, key, message, --  status
        ['POST',   '9', {"f":25, "s":50}, 'Created'],
        ['GET',    '9', None, {"f":25, "s":100500}],
        ['DELETE', '9', None, 'Ok'],
    ]
    send_request(sessions)
