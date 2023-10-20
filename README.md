# Burp2Json

Burp2Json consists of a Burp extension (Burp2Json) that takes requests from Burp and generates JSON call templates for those requests, a python module (also called Burp2Json) that has functionality to read JSON call templates and make HTTP calls based on those templates, and an example python code and REST service to use those.

## Building Burp extension
Run
```gradle build```
This will create a build/libs/Burp2Json-1.0.jar file. Open the Extensions tab in Burp and add this jar file as extension

## Installing python module

Run once:
```
pip install -e .
```
# Using example code

Run the sample web service

Depending on your version of flask:

Flask 2.0.x :
```
> export FLASK_APP=sample_server
> flask run
```
Flask 3.0.x
```
> flask --app sample_server run
```
This will run a web server on http://localhost:5000 provising a simple REST web service. The source code for the service is in sample_service.py

Start Burp proxy on port 8080.

Now read and run the example code
```
> python examples.py
```

# Using all this for your own tests

1. Collect the REST requests you want in Burp proxy or repeater. 
2. In Proxy or Target tool select the requests you want to export.
3. Right-click on the selected requests, choose Extension -> Burp2Json -> Burp2Json (# request(s) selected) - generate . This will generate a JSON array ([]) consisting of JSON objects for each request and place it in the clipboard
4. Open a new test file in any editor and paste the generated JSON code.
5. Save the JSON file in your working directory.
6. Write a python script that uses Burp2Python module (import Burp2Python), loads your JSON file (b2j = burp2json.Burp2Json("sample.json")) and executes your test scenarios. Use examples.py for inspiration

# Security

***Burp2Json disables SSL server certificate validation and warnings by default because this is what we generally want in test scenarios*** . Do not use it in any kind of scenario where transport level security is important.

You can enable server certificate validation by doing:
```
b2j = burp2json.Burp2Json("sample.json")
b2j.ssl_verify = true
```
# Features

1. Burp2Json supports any kind of HTTP verbs, and different kind of body content (i.e. url-encoded body paramters, multipart/form-data, JSON, XML, and arbitrary body data). Binary body data, particularly large blobs of binary data probably will not work very well, or not at all
2. Requests can be customised by adding headers, cookies, query parameters, POST url-encoded parameters. If a header. cookie, query paramter or POST url-encoded parameter with the same name already exists in the JSON template it will be replaced. The tool does not support multiple paramters with the same name
3. Requests can be customised by substituting values in JSON body and request path. To facilitate this, you need to create placeholders in JSON templates. See examples.py
4. Burp2Json python module can use python requests session object. This allows using cookie-based sessions in multi-step scenarios and SSL client certificate authentication.
5. do_request() method returns python requests response object. You can analyze all aspects of the response.
6. do_all() method accepts a response_handler function as a parameter. It can be used, for example, to print the result of every request made in CSV format, and then easily analyze the output in a spreadsheet app that allows sorting and filtering

# Use cases

1. Automating authentication/authorization testing. You can run a set of requests with/without a particular cookie, with/without Authorization header , with/without client SSL certificate
2. Implementing multi-step authentication scenarios before running access control tests
3. Simplifying access control tests. Write an authentication sequence, call it to obtain the necessary tokens, pass the tokens to do_all(). Make all requests as different users, output as CSV, check where the actual behaviour deviates from expectations
4. Reproducability. You can easily replay your test scenarios (after fixes has been implemented, in a different environment, with different user accounts, etc.)