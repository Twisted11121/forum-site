from flask import Flask, render_template, request, session
import sqlite3


app = Flask(__name__)
database = 'database.db'
login_db = 'login.db'

con = sqlite3.connect("login.db")
cur = con.cursor()
cur.execute("CREATE TABLE login(username, password)")
con.commit()

app.secret_key = "WellOffToVisitYourMother!" 


#finish forum database


@app.route('/')
def index():

    #Add session
    if 'username' in session:
        return render_template('index.html')

    return render_template('login_page.html')

@app.route("/login",  methods=['POST'])
def login():
    
    con = sqlite3.connect("login.db")
    cur = con.cursor()


    try:
        username = request.form["username"]
        password = request.form["password"]
        try:
            info = cur.execute("SELECT * FROM login WHERE username={username}")
            info2 = info.fetchall()
            if password in info2:
                return render_template('/')
        except:
            return render_template('register-acc.html')

    except:
        pass