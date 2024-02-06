import hashlib
import base64
import random
import shutil
import flask
import json
import time
import os

import secret_file

from flask import request, redirect
from werkzeug.middleware.proxy_fix import ProxyFix

UPGRADE_TO_HTTPS = False
SAVING_DIR = "./save/"
CONTENT_DIR = "./public/"

captchas = {}

def create_token(username, passhash) -> str:
    return "" + username + "-" + sha(username + passhash + secret_file.str1) + sha(passhash + secret_file.str2)

def sha(string: str) -> str:
    return hashlib.sha256(str.encode(string)).hexdigest()

def shrink_captchas() -> None:
    global captchas
    now = round(time.time())
    new = dict(captchas)
    for i in captchas:
        if new[i] + 60 * 5 < now:
            del new[i]
    captchas = dict(new)

def create_captcha() -> str:
    shrink_captchas()

    now = round(time.time())
    out = []

    for _ in range(random.randint(10, 20)):
        var_name = ""
        for _ in range(random.randint(5, 15)):
            var_name += random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

        var_val = ""
        for _ in range(random.randint(25, 45)):
            var_val += random.choice("          ;;;;;;;;;;abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890123456789^$*(&!@)*TYH(*6&*(!$^@*(&^}{>})))")

        out.append([var_name, var_val, True])

    for _ in range(random.randint(5, 25)):
        x = random.randint(0, len(out) - 2)
        y = random.randint(x + 1, len(out) - 1)

        var_val = ""
        for _ in range(random.randint(25, 45)):
            var_val += random.choice("          ;;;;;;;;;;abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890123456789^$*(&!@)*TYH(*6&*(!$^@*(&^}{>})))")

        out.insert(y, [out[x][0], var_val, False])

    var_name = random.choice(out)[0]

    for i in range(len(out) - 1, -1, -1):
        if out[i][0] == var_name:
            captchas[out[i][1]] = now
            break

    return '<script>let captcha;eval(atob("' + bytes.decode(base64.b64encode(str.encode(";".join([f"{'let ' if i[2] else ''}{i[0]}='{i[1]}'" for i in out]) + f";captcha={var_name};"))) + '"))</script>'

def validate_captcha(value: str) -> bool:
    shrink_captchas()

    return value in captchas

def ensure_file(path: str, *, default_value: str="", folder: bool=False) -> None:
    if os.path.exists(path):
        if folder and not os.path.isdir(path):
            os.remove(path)
            os.makedirs(path)
        elif not folder and os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
            f = open(path, "w")
            f.write(default_value)
            f.close()
    else:
        if folder:
            os.makedirs(path)
        else:
            f = open(path, "w")
            f.write(default_value)
            f.close()

def get_user_info(username) -> dict[str, str]:
    return json.loads(open(f"{SAVING_DIR}users/{username}.json", "r").read())

def get_user_messages(username) -> list[dict]:
    return json.loads(open(f"{SAVING_DIR}messages/{username}.json", "r").read())

def create_static_route(file):
    x = lambda var = None: flask.send_file(f"{CONTENT_DIR}{file}")
    x.__name__ = file
    return x

def content_type_response(content, content_type: str="text/html") -> flask.Response:
    response = flask.make_response(content)
    response.headers["Content-Type"] = content_type
    return response

def create_captcha_route(file):
    x = lambda: content_type_response(open(f"{CONTENT_DIR}{file}", "r").read().replace("{{CAPTCHA}}", create_captcha()))
    x.__name__ = file
    return x

def api_account_signup():
    x = json.loads(request.get_data())

    # Check captcha
    if not validate_captcha(x["captcha"]):
        flask.abort(403)

    x["username"] = x["username"].lower()

    # Make sure user doesn't exist
    try:
        get_user_info(x["username"])
        flask.abort(401)
    except FileNotFoundError:
        pass

    # Validate username and passhash
    if len(x["passhash"]) != 64 or x["passhash"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855":
        flask.abort(400)

    if len(x["username"]) < 1 or len(x["username"]) > 24:
        flask.abort(400)

    for i in x["passhash"]:
        if i not in "abcdef0124356789":
            flask.abort(400)

    for i in x["username"]:
        if i not in "abcdefghijklmnopqrstuvwxyz0123456789_":
            flask.abort(400)

    token = create_token(x["username"], x["passhash"])

    ensure_file(
        f"{SAVING_DIR}users/{x['username']}.json",
        default_value=json.dumps({
            "token": token
        })
    )

    ensure_file(
        f"{SAVING_DIR}messages/{x['username']}.json",
        default_value="[]"
    )

    return content_type_response(
        json.dumps({
            "token": token
        }), "application/json"
    )

def api_account_login():
    x = json.loads(request.get_data())

    x["username"] = x["username"].lower()

    for i in x["username"]:
        if i not in "abcdefghijklmnopqrstuvwxyz0123456789_":
            flask.abort(400)

    user_info = {}
    try:
        user_info = get_user_info(x["username"])
    except FileNotFoundError:
        flask.abort(401)

    token = create_token(x["username"], x["passhash"])

    if user_info["token"] != token:
        flask.abort(400)

    return content_type_response(
        json.dumps({
            "token": token
        }), "application/json"
    )

def api_messages_get():
    username = request.cookies["token"].split("-")[0]
    token = request.cookies["token"]

    for i in username:
        if i not in "abcdefghijklmnopqrstuvwxyz0123456789_":
            flask.abort(400)

    if token != get_user_info(username)["token"]:
        flask.abort(403)

    return content_type_response(
        json.dumps(get_user_messages(username)),
        "application/json"
    )

def api_messages_post_(user):
    for i in user:
        if i not in "abcdefghijklmnopqrstuvwxyz0123456789_":
            flask.abort(400)

    x = json.loads(request.get_data())

    if len(x["message"]) == 0 or len(x["message"]) > 512 or len(x["name"]) > 24:
        flask.abort(401)

    time.sleep(0.25) # Artifical delay to prevent spamming

    messages = [{"message": x["message"], "name": x["name"], "time": round(time.time())}] + get_user_messages(user)
    open(f"{SAVING_DIR}messages/{user}.json", "w").write(json.dumps(messages))

    return "200 OK"

def message_(user):
    user = user.lower()

    for i in user:
        if i not in "abcdefghijklmnopqrstuvwxyz0123456789_":
            flask.abort(404)

    try:
        get_user_info(user)
        return content_type_response(open(f"{CONTENT_DIR}message.html", "r").read().replace("{{USER}}", user), "text/html")
    except FileNotFoundError:
        flask.abort(404)

ensure_file(SAVING_DIR, folder=True)
ensure_file(f"{SAVING_DIR}users", folder=True)
ensure_file(f"{SAVING_DIR}messages", folder=True)

app = flask.Flask(__name__)

app.route("/", methods=["GET"])(create_static_route("index.html"))
app.route("/login", methods=["GET"])(create_static_route("login.html"))
app.route("/signup", methods=["GET"])(create_captcha_route("signup.html"))
app.route("/messages", methods=["GET"])(create_static_route("messages.html"))
app.route("/logout", methods=["GET"])(create_static_route("logout.html"))
app.route("/m/<path:user>", methods=["GET"])(message_)

app.route("/css/base.css", methods=["GET"])(create_static_route("css/base.css"))
app.route("/js/base.js", methods=["GET"])(create_static_route("js/base.js"))

app.route("/api/account/signup", methods=["POST"])(api_account_signup)
app.route("/api/account/login", methods=["POST"])(api_account_login)
app.route("/api/messages/list", methods=["GET"])(api_messages_get)
app.route("/api/messages/post/<path:user>", methods=["POST"])(api_messages_post_)

app.errorhandler(404)(create_static_route("404.html"))

if UPGRADE_TO_HTTPS:
    app.wsgi_app = ProxyFix(app.wsgi_app)

    @app.before_request
    def enforce_https():
        if not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

if __name__ == "__main__":
    app.run(port=80, debug=True, host="0.0.0.0")
