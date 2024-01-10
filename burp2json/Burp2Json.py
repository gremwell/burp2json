import json
import requests
from string import Template
import urllib3


class Burp2Json:
    def __init__(self, filename=None, json_string=None, data=None):
        if filename != None:
            self._requests = json.load(open(filename, "r"))
        elif json_string != None:
            self._requests = json.loads(json_string)
        elif data != None:
            self._requests = data
        else:
            self._requests = []
        self._ssl_warnings = False
        self._ssl_verify = False
        self._proxy = None
        self._target = None
        self._session = requests.Session()
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    @property
    def ssl_verify(self):
        return self._ssl_verify

    @ssl_verify.setter
    def ssl_verify(self, value):
        self._ssl_verify = value

    @property
    def proxy(self):
        return self._proxy

    @proxy.setter
    def proxy(self, value):
        self._proxy = value
        self._session.proxies.update({"http": self._proxy, "https": self._proxy})

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    def request_by_path(self, method, path):
        return [
            item
            for item in self._requests
            if (item["path"] == path and item["method"] == method)
        ][0]
    
    def do_request_by_path(self, method, path, target = None, session=None, extra_cookies=None, extra_headers=None, get_params=None, post_params=None, json_params=None, path_params=None, files=None):
        return self.do_request(self.request_by_path(method, path), target, session, extra_cookies, extra_headers, get_params, post_params, json_params, path_params, files)

    def request_by_comment(self, comment):
        return [item for item in self._requests if (item["comment"] == comment)][0]
    
    def do_request_by_comment(self, comment, target = None, session=None, extra_cookies=None, extra_headers=None, get_params=None, post_params=None, json_params=None, path_params=None, files=None):    
        return self.do_request(self.request_by_comment(comment), target, session, extra_cookies, extra_headers, get_params, post_params, json_params, path_params, files)
    

    def get_all(self):
        return self._requests

    def do_request(
        self,
        request,
        target = None,
        session=None,
        extra_cookies=None,
        extra_headers=None,
        get_params=None,
        post_params=None,
        json_params=None,
        path_params=None,
        files=None,
    ):
        if session == None:
            session = self._session

        if target == None:
            target = self._target   

        my_req = request.copy()

        # Handle REST-style path parameters
        if path_params != None:
            my_req["path"] = Template(request["path"]).substitute(path_params)

        # add extra cookies
        if extra_cookies != None:
            for cookie_name in extra_cookies.keys():
                session.cookies.set(cookie_name, extra_cookies[cookie_name])

        # add extra headers
        if extra_headers != None:
            my_req["headers"] = extra_headers | request["headers"]

        # handle get parameters
        if get_params != None:
            my_req["params"] = request["params"] | get_params

        # handle body data
        if post_params != None:
            # if we have body url-encoded params
            if isinstance(request["data"], dict):
                my_req["data"] = request["data"] | post_params
            else:
                # The body is not URL-encoded, it is some other format.
                # We assume that it is a template and do variable substitution
                my_req["data"] = Template(request["data"]).substitute(post_params)

        # Handle json
        if "json" in request and json_params != None:
            my_req["json"] = json.loads(
                Template(request["json"]).substitute(json_params)
            )
        else:
            if "json" in request:
                my_req["json"] = json.loads(request["json"])

        # Handle multipart/form-data
        if files != None:
            my_req["files"] = files

        # Handle missing keys
        for name in ["params", "data", "json", "headers", "files"]:
            if not (name in my_req):
                my_req[name] = None

        return session.request(
            method=my_req["method"],
            url=target + my_req["path"],
            params=my_req["params"],
            data=my_req["data"],
            json=my_req["json"],
            headers=my_req["headers"],
            files=my_req["files"],
            verify=self._ssl_verify,
        )

    def do_all(
        self,
        target = None,
        session=None,
        extra_cookies=None,
        extra_headers=None,
        get_params=None,
        post_params=None,
        json_params=None,
        path_params=None,
        files=None,
        handle_response=None,
    ):
        for req in self._requests:
            resp = self.do_request(
                req,
                target,
                session,
                extra_cookies,
                extra_headers,
                get_params,
                post_params,
                json_params,
                path_params,
                files,
            )
            if handle_response != None:
                handle_response(req, resp)
