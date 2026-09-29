from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return """"
    <h1>ProjectFlow</h1>
    </h2>Система управления проектами</h2>
    <p>Добро пожаловать!</p>
    """

if __name__ == "__main__":
    app.run(debug = True)