from flask import Flask, render_template, request, session, jsonify
import sqlite3


app = Flask(__name__)
database = 'database.db'
login_db = 'login.db'

con_login = sqlite3.connect("login.db")
cur_login = con_login.cursor()
cur_login.execute("CREATE TABLE IF NOT EXISTS login(username, password)")
con_login.commit()
con_login.close()
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
    con_login = sqlite3.connect("login.db")
    cur_login = con_login.cursor()
    

    try:
        username = request.form["username"]
        password = request.form["password"]

        info = cur_login.execute(f"SELECT * FROM login WHERE username={username}")
        info2 = info.fetchall()
        if password in info2:
            con_login.commit()
            con_login.close()
            return render_template('/')
        
    except:
        con_login.close()
        return render_template('register-acc.html')

@app.route('/registerPage')
def showRegi():
    return render_template('register-acc.html') 

@app.route("/register", methods=['POST'])
def register():

    con_login = sqlite3.connect("login.db")
    cur_login = con_login.cursor()

    username = request.form["username"]
    password = request.form["password"]
    
    reg_user = cur_login.execute(f"INSERT INTO login(username, password) VALUES ({username}, {password})")
    con_login.commit()
    con_login.close()
    return jsonify({'success': True})


if __name__ == "__main__":
    app.run(debug=True)