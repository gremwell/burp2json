import burp2json
import requests

# Run the sample web service before using this example
# Depending on your version of flask:
# Flask 2.0.x :
# > export FLASK_APP=sample_server
# > flask run
# Flask 3.0.x
# flask --app sample_server run

# Read request templates from file
b2j = burp2json.Burp2Json("sample.json")

# Most simple use case - run all requests without modification
# Don't use proxies, and don't do anything with responses
print("Running all requests, don't expect any output")
b2j.do_all(prefix="http://127.0.0.1:5000")

# Now let's suppose we want to do something with responses, such as look at the response codes
# We will pass this function to do_all to print results in CSV format
def handle_response(req, resp) :
    print("{},{},{},{}".format(req["comment"], req["method"], req["path"], resp.status_code))

# Now let's run all requests and print results
print("Running all requests, now with CSV output")
b2j.do_all(prefix="http://127.0.0.1:5000", handle_response=handle_response)

# We can also run our requests through Burp, so we set proxy configuration
proxies = {
        'http': 'http://127.0.0.1:8080',
        'https': 'http://127.0.0.1:8080',
}
session = requests.Session()
session.proxies.update(proxies)
print("Running all requests through Burp, expecting it to listen on 127.0.0.1:8080")
b2j.do_all(prefix="http://127.0.0.1:5000", handle_response=handle_response, session=session)

print("Will execute a scenario. Create an item, do a search, read the response, then call found items one by one")

b2j = burp2json.Burp2Json("parameterized.json")
create = b2j.request_by_comment("add item")

print("Creating a new item")
resp = b2j.do_request(create, prefix="http://127.0.0.1:5000", session=session, json_params={"name":"bob", "value":"20"})
print("Got response: stus coce {}, content {}".format(resp.status_code, resp.json()))

search = b2j.request_by_path("GET","/api/search")

print("Calling search")
resp = b2j.do_request(search, prefix="http://127.0.0.1:5000", session=session, get_params={"text":"20"})
print("Got response code: {}".format(resp.status_code))
if(resp.status_code == 200) :
    j = resp.json()
    print("Got response body: {}".format(j))
    print("Now will get item ids from body and request items one by one")
    get_item = b2j.request_by_comment("get item")
    for id in j.keys() :
        r = b2j.do_request(get_item, prefix="http://127.0.0.1:5000",  session=session, path_params={"id":id})
        print("Got item {} : {}".format(id, r.json()))






