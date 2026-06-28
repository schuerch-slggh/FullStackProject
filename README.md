# hello-world-fswd


### Setup Python environment
```
python -m venv .venv
source .venv/bin/activate  # On MacOS
 .venv\Scripts\activate  # On Windows
pip install -r requirements.txt 
```
## Run once to activate debug mode

``` bash/powershell
$env:FLASK_DEBUG="1"
```

### Run the App

````
flask --app main run
````

### Visit in Browser
- Open http://127.0.0.1:5000 to see the "Hello, World!" message.

