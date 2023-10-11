from argparse import ArgumentParser
from os import remove
from urllib.parse import urlsplit

from bottle import Bottle, request, response, SimpleTemplate
from exiftool import ExifTool
from requests import get
from waitress import serve


IMAGE_FILE_EXTENSIONS = {
    "gif",
    "jpg",
    "jpeg",
    "png",
    "svg",
    "tif",
    "tiff",
}
STYLE_ENDPOINT = "/style.css"
BASE_TEMPLATE = """<html>
    <head>
        <title>Image Metadata</title>
        <link rel="stylesheet" href="/style.css">
    </head>
    <body>
        <div id="main">
            <h1 class="orange">Metadata Viewer</h1>
            <div>
                <form method="post">
                    <input type="text" id="url" name="url" class="green glowy">
                    <input type="submit" value=">" id="get" class="green glowy">
                </form>
            </div>
            {}
        </div>
    </body>
</html>"""

MESSAGE_TEMPLATE = SimpleTemplate(BASE_TEMPLATE.format("""
<div>
    <p class="blue">{{ message }}</p>
</div>
"""))

ERROR_TEMPLATE = SimpleTemplate(BASE_TEMPLATE.format("""
<div>
    <p class="error">{{ message }}</p>
</div>
"""))

TABLE_TEMPLATE = SimpleTemplate(BASE_TEMPLATE.format("""
<div>
    <table>
        % for k, v in items:
        <tr>
            <td>{{ k }}</td>
            <td>{{ v }}</td>
        </tr>
        % end
    </table>
</div>
<div>
    <form action="/strip" method="post">
        <input type="hidden" name="url", value="{{ url }}">
        <input type="submit" value="Download Stripped" id="download" class="green glowy">
    </form>
</div>
"""))

STYLE = """
body{
    padding-inline: 5em;
    padding-top: 5em;
    background-color: #263238;
    font-family: Consolas, monaco, monospace;
}

#main {
    margin: auto;
    width: 40em;
    background-color: #546e7a;
    border-radius: 1em;
    padding: 1em;
    text-align: center;
}

form {
    padding: 1em;
    margin: auto;
}

input {
    background-color: #455a64;
    border-color: #37474f;
    color: #9accc7;
    padding: .5em;
    font-family: Consolas, monaco, monospace;
}

input[type=text] {
    margin: auto;
    width: 50em;
    max-width: 90%;
}

h1 {
    text-align: center;
}

p {
    text-align: center;
    font-weight: bold;
}

table {
    width: 90%;
    margin: auto;
}

.green {
    color: #22ff56;
}

.glowy:hover, .green-glowy:focus {
    box-shadow: 0 0 .75em;
}

.glowy:active {
    box-shadow: 0 0 .75em #cbff22;
}

.error{
    color: #ff4375;
}

.blue {
    color: #22cbff;
}

.orange {
    color: #ff5622;
}

#get {
    width: 3em;
}
"""

# Strip escape characters
bad_chars = "".join([chr(char) for char in range(1,32)] + ['\\', ' '])
sanitize = str.maketrans("", "", bad_chars)

app = Bottle()
exif = ExifTool()


def get_safe_filename_from_url(url):
    spliturl = urlsplit(url)
    filename = spliturl.path.split("/")[-1]
    safe = filename.translate(sanitize)
    return safe


@app.get(STYLE_ENDPOINT)
def style():
    return STYLE


@app.get("/")
def landing():
    return MESSAGE_TEMPLATE.render(message="Enter image url")


@app.post("/")
def meta():
    url = request.forms.get("url")
    
    if not url:
        return ERROR_TEMPLATE.render(message="No url provided")

    if url.split(".")[-1] not in IMAGE_FILE_EXTENSIONS:
        return ERROR_TEMPLATE.render(message="URL must link to a gif, jpeg, png, svg, or tiff file")
    
    try:
        image = get(url, stream=True)
    except Exception:
        return ERROR_TEMPLATE.render(message="Failed to fetch image")

    safe_filename = get_safe_filename_from_url(url)
    filepath = "/tmp/{}".format(safe_filename)
    try:
        with open(filepath, "wb+") as f:
            for chunk in image:
                f.write(chunk)
        meta = exif.get_metadata(f.name)
    finally:
        remove(filepath)

    return TABLE_TEMPLATE.render(items=sorted(meta.items()), url=url)


@app.post("/strip")
def strip():
    url = request.forms.get("url")
    
    if not url:
        return MESSAGE_TEMPLATE.render(message="No url provided")
    if url.split(".")[-1] not in IMAGE_FILE_EXTENSIONS:
        return MESSAGE_TEMPLATE.render(message="URL must link to a gif, jpeg, png, svg, or tiff file")
    
    try:
        image = get(url, stream=True)
    except Exception:
        return MESSAGE_TEMPLATE.render(message="Failed to fetch image")

    safe_filename = get_safe_filename_from_url(url)
    filepath = "/tmp/{}".format(safe_filename)
    try:
        with open(filepath, "wb+") as f:
            for chunk in image:
                f.write(chunk)
        
        args = ["-all=", "-tagsFromFile", "@"]
        exif.execute(b"-All", b"-overwrite_original", f.name.encode())

        with open(filepath, "rb") as f:
            content = f.read()

        response.set_header("Content-Type", "application/octet-stream")
        response.set_header("Content-Disposition", "attachment; filename={}".format(safe_filename))
        return content
    finally:
        remove(filepath)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-a", "--address", default="0.0.0.0")
    parser.add_argument("-p", "--port", default=80)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    try:
        exif.start()
        if args.debug:
            app.run(host=args.address, port=args.port, debug=args.debug)
        else:
            serve(app, listen="{}:{}".format(args.address, args.port))
    except Exception as e:
        print(e)
    finally:
        if exif.running:
            exif.terminate()
        app.close()

