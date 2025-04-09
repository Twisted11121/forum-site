from flask import Flask, render_template

app = Flask(__name__)
import random
import requests

@app.route("/")
def test():
    img_url = requests.get("https://cataas.com/cat?json=true").json()
    image=f"https://cataas.com/cat/{img_url["id"]}"
    print(image)
    return render_template("test.html", url=image)

app.run(debug=True, port=5000)


#afn["result"]["pictures"]["large"]