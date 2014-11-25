# coding: utf-8

import re
import urllib
import urllib2
from urllib import urlencode
from urllib2 import HTTPError

from flask import Flask
from flask import make_response
from flask import request
from flask import Response


API_SERVER = 'https://xxx.xxx.xxx'


app = Flask(__name__)


@app.route("/")
def index():
    return "Hello World!"


@app.route("/login/", methods=['POST'])
def login():
    # request.json.get('username')
    # request.cookies.get('sessionid')
    username = request.form.get('username')
    password = request.form.get('password')
    source = request.form.get('source')

    try:
        sessionid, response = login_by_user_password_cookies(username, password, source)
        resp = make_response(response.read())
        resp.set_cookie('sessionid', sessionid)
        resp.content_type = response.headers.typeheader
        resp.status_code = response.getcode()
        return resp
    except HTTPError as e:
        resp = make_response(e.read())
        resp.content_type = e.headers.typeheader
        resp.status_code = e.getcode()
        return resp
    except Exception as e:
        sessionid = None
        return '', 500


@app.route("/logout/", methods=['GET'])
def logout():
    sessionid = request.cookies.get('sessionid')
    req = urllib2.Request(API_SERVER + '/api/logout/')
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor()) 
    if sessionid:
        req.add_header("Cookie", 'sessionid=' + sessionid)
    response = opener.open(req)
    resp = make_response(response.read())
    resp.set_cookie('sessionid', '', expires=0)
    resp.content_type = response.headers.typeheader
    resp.status_code = response.getcode()
    return resp
    

@app.route("/users/", methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'OPTION'])
def users():
    sessionid = request.cookies.get('sessionid')
    try:
        data, sock = invoke_api(sessionid)
        resp = make_response(data)
        resp.set_cookie(sock.headers.get('set-Cookie'))
        resp.content_type = sock.headers.typeheader
        resp.status_code = sock.getcode()
        return resp
    except HTTPError as e:
        resp = make_response(e.read())
        resp.content_type = e.headers.typeheader
        resp.status_code = e.getcode()
        if "Your connection is expired, please login again" in resp.get_data():
            resp.set_cookie('sessionid', '', expires=0)
        return resp
    except Exception as e:
        return '', 500

# test api server
def login_by_user_password_cookies(user_id, password, source):
    req = urllib2.Request(API_SERVER + '/api/login/')
    data = urlencode({
        'username': user_id,
        'password': password,
        'source': source
    })
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())  
    response = opener.open(req, data)
    set_cookie = response.headers.get('set-cookie')
    sessionid = re.match('.*?sessionid=(.*?);', set_cookie).group(1)
    return sessionid, response


def invoke_api(sessionid):
    req = urllib2.Request(API_SERVER + '/api/privilege/system_user/?format=json')
    if sessionid:
        req.add_header("Cookie", 'sessionid=' + sessionid)
    opener=urllib2.build_opener(urllib2.HTTPHandler(debuglevel=2))
    sock=opener.open(req)
    content=sock.read()
    sock.close()
    return content, sock


if __name__ == "__main__":
    app.run()
