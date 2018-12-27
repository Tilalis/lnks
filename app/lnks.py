import json

from flask import Flask
from flask import request, redirect, render_template, make_response, escape

from app.utils import LinksDB

links = Flask(__name__, template_folder='templates')
db = LinksDB('lnks.db')


@links.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        alias = request.json.get('alias')
        link = request.json.get('link')

        if not (link.startswith('http://') or link.startswith('https://')):
            link = 'http://' + link

        error_response = (
            json.dumps({
                "status": "error"
            }, indent=4),
            400
        )

        if link is None or link == "" or alias is None or alias == "":
            return error_response

        success = db.alias(link, alias)

        if not success:
            return error_response

        return (
            json.dumps({
                "status": "done",
                "url": "{base_url}{alias}".format(
                    base_url=request.base_url,
                    alias=alias
                )
            }, indent=4),

            200
        )

    return render_template('index.html', url=request.base_url)


@links.route("/<alias>", methods=["GET"])
def resolve(alias):
    def _response(url, code=302, template='redirect.html'):
        response = make_response(
            render_template(template, url=escape(url)),
            code
        )

        response.headers['Location'] = link

        return response

    link = db.link(alias)

    if link is None:
        return _response('/')

    return _response(link)

