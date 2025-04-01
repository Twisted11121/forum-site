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

    if 'username' in session:
        return render_template('index.html')

    return render_template('login_page.html')

@app.route("/login",  methods=['POST'])
def login():
    con_login = sqlite3.connect("login.db")
    cur_login = con_login.cursor()
    

    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        session['username'] = request.form['username']
        cur_login.execute("SELECT password FROM login WHERE username=?", (username,))
        result = cur_login.fetchone()

        if result is not None:
            stored_password = result[0]

            if password == stored_password:  # Compare the provided password with the stored password
                return jsonify(success=True)
            else:
                return jsonify(success=False, error="Invalid username or password"), 401
        else:
            return jsonify(success=False, error="Invalid username or password"), 401

@app.route('/registerPage')
def showRegi():
    return render_template('register-acc.html') 

@app.route("/register", methods=['POST'])
def register():

    con_login = sqlite3.connect("login.db")
    cur_login = con_login.cursor()

    username = request.form["username"]
    password = request.form["password"]
    
    reg_user = cur_login.execute("INSERT INTO login (username, password) VALUES (?, ?)", (username, password))
    con_login.commit()
    con_login.close()
    return jsonify({'success': True})


if __name__ == "__main__":
    app.run(debug=True)