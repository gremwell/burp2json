from flask import Flask
from flask import request

app = Flask(__name__)

records = {'1' : {"aaa":"bbb"}}
id = 2

def add(data) :
    global records
    global id
    records[str(id)] = data
    id = id + 1

def get(id) :
    return records[id]

# GET endpoint - accepts query parameters
@app.get('/api/search')
def search():
    searchword = request.args.get('text', '')
    result = {}
    for k in records.keys() :
        for v in records[k].values() :
            if v.find(searchword) != -1 :
                result[k] = records[k]
    return result

# GET endpoint - does not expect any parameters
@app.get('/api/items')
def getall() :
    return records

# GET endpoint - accepts path paramters
@app.get('/api/item/<id>')
def get_item(id):
    return records[id]

# POST endpoint - expects data JSON
@app.post('/api/items')
def create_entry():
    data = request.get_json(force=True)
    add(data)
    return data

#POST endpoint - expects multipart/form-data
@app.post('/api/upload')
def upload() :
    file = request.files['file']
    for line in file.stream :
        [k, v] = line.decode().rstrip().split(',')
        add({k:v})
    return("Received file " + file.filename)

#