FIXME

Run once:
```
cd $HOME
git clone git@github.com:gremwell/burp2json.git
cd burp2json
pip install -e .
```

In a project:
```
cp $HOME/burp2json/example.py .
python3 burp2json_example.py
```

Using example:

Run the sample web service before using this example
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

Start Burp proxy on port 8080
```
> python examples.py
```
