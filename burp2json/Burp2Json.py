import json
import requests
from string import Template
import urllib3


class Burp2Json:
    def __init__(self, filename=None, json_string=None, data=None, proxy = None, target = None):
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
        self._session = requests.Session()
        if proxy != None:
            self._proxy = proxy
            self._session.proxies.update({"http": self._proxy, "https": self._proxy})
        else:
            self._proxy = None
        if target != None:
            self._target = target
        else:
            self._target = None

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
    
    def do_request_by_path(self, method, path, target = None, session=None, extra_cookies=None, extra_headers=None, get_params=None, post_params=None, json_params=None, path_params=None, files=None, handle_response=None,handle_response_data=None, allow_redirects=False):
        return self.do_request(self.request_by_path(method, path), target, session, extra_cookies, extra_headers, get_params, post_params, json_params, path_params, files, handle_response, handle_response_data, allow_redirects)

    def request_by_comment(self, comment):
        return [item for item in self._requests if (item["comment"] == comment)][0]
    
    def do_request_by_comment(self, comment, target = None, session=None, extra_cookies=None, extra_headers=None, get_params=None, post_params=None, json_params=None, path_params=None, files=None, handle_response=None, handle_response_data=None, allow_redirects=False):    
        return self.do_request(self.request_by_comment(comment), target, session, extra_cookies, extra_headers, get_params, post_params, json_params, path_params, files, handle_response, handle_response_data, allow_redirects)

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
        handle_response=None,
        handle_response_data=None,
        allow_redirects=False
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
            if "headers" in request:
                my_req["headers"] = extra_headers | request["headers"]
            else:
                my_req["headers"] = extra_headers

        # handle get parameters
        if get_params != None:
            if "params" in request:
                my_req["params"] = request["params"] | get_params
            else:
                my_req["params"] = get_params

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

        resp = session.request(
            method=my_req["method"],
            url=target + my_req["path"],
            params=my_req["params"],
            data=my_req["data"],
            json=my_req["json"],
            headers=my_req["headers"],
            files=my_req["files"],
            verify=self._ssl_verify, 
            allow_redirects=allow_redirects
        )
        if handle_response != None:
            handle_response(my_req, resp, handle_response_data)
        return resp

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
        handle_response_data=None,
        allow_redirects=False
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
                handle_response,
                handle_response_data,
                allow_redirects
            )

    def do_selected_by_comment(self, selected, target = None,
        session=None,
        extra_cookies=None,
        extra_headers=None,
        get_params=None,
        post_params=None,
        json_params=None,
        path_params=None,
        files=None,
        handle_response=None,
        handle_response_data=None,
        allow_redirects=False
    ):
        for comment in selected:
                resp = self.do_request_by_comment(
                comment=comment,
                target=target,
                session=session,
                extra_cookies=extra_cookies,
                extra_headers=extra_headers,
                get_params=get_params,
                post_params=post_params,
                json_params=json_params,
                path_params=path_params,
                files=files,
                allow_redirects=allow_redirects
                )
                if handle_response != None:
                    handle_response(self.request_by_comment(comment), resp, handle_response_data) 