# crueltouch
Live website [here](https://crueltouch.com/)
## Setup

The first thing to do is to clone the repository:

```sh
$ git https://github.com/adamspd/crueltouch.git
$ cd crueltouch
```

Create a virtual environment to install dependencies in and activate it:

```sh
$ virtualenv2 --no-site-packages env
$ source env/bin/activate
```

Then install the dependencies:

```sh
(env)$ pip install -r requirements.txt
```
Note the `(env)` in front of the prompt. This indicates that this terminal
session operates in a virtual environment set up by `virtualenv2`.

Once `pip` has finished downloading the dependencies:
```sh
(env)$ python3 manage.py runserver
```
And navigate to `http://127.0.0.1:8000/`.

In order to test the purchase flows, fill in the account details in
`project/gc_app/views.py` to match your **SANDBOX** developer credentials.
