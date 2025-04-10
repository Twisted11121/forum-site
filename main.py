from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import sqlite3
from datetime import datetime
import re

app = Flask(__name__)
database = 'threads.db'
login_db = 'login.db'

def i_login_db():
    con_login = sqlite3.connect(login_db)
    cur_login = con_login.cursor()
    cur_login.execute("CREATE TABLE IF NOT EXISTS login(username TEXT, password TEXT, userPic TEXT)")
    con_login.commit()
    con_login.close()

def thread_db():
    con = sqlite3.connect(database)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            creator TEXT NOT NULL,
            timestamp TIME NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (thread_id) REFERENCES threads (id) ON DELETE CASCADE
        )
    ''')
    con.commit()
    con.close()

i_login_db()
thread_db()

app.secret_key = "WellOffToVisitYourMother!" 

@app.route('/')
def index():
   

    if 'username' in session:
        return render_template('index.html')

    return render_template('login_page.html')

@app.route('/displayThreads')
def displayThreads():
    con = sqlite3.connect(database)
    cur = con.cursor()
    threads = cur.execute('SELECT * FROM threads').fetchall()
    con.close()

    return render_template('threads.html', threads=threads)

@app.route("/login", methods=['POST'])
def login():
    con_login = sqlite3.connect(login_db)
    cur_login = con_login.cursor()

    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]

        cur_login.execute("SELECT password FROM login WHERE username=?", (username,))
        result = cur_login.fetchone()

        if result is not None:
            stored_password = result[0]
            if password == stored_password:
                session['username'] = username
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
    con_login = sqlite3.connect(login_db)
    cur_login = con_login.cursor()

    username = request.form["username"]
    password = request.form["password"]
    
    defaultUserPic = "https://static.wikia.nocookie.net/frutigeraero/images/2/2a/Icon1.png/revision/latest?cb=20241230231133"

    cur_login.execute("INSERT INTO login (username, password, userPic) VALUES (?, ?, ?)", (username, password, defaultUserPic))
    con_login.commit()
    con_login.close()
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template("login_page.html")

@app.route('/create_thread', methods=['GET', 'POST'])
def create_thread():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        username = session['username']
        now1 = datetime.now()
        formatted_date_time = now1.strftime("%d/%m/%Y %H:%M")


        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute('INSERT INTO threads (title, content, creator, timestamp) VALUES (?, ?, ?, ?)', (title, content, username, formatted_date_time))
        con.commit()
        con.close()
        
        return redirect(url_for('displayThreads'))
    return render_template('create_thread.html')

@app.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
def thread(thread_id):
    con = sqlite3.connect(database)
    cur = con.cursor()
    conLog = sqlite3.connect(login_db)
    curLog = conLog.cursor()

    if request.method == 'POST':
        content = request.form['content']
        username = session['username']  

        cur.execute('INSERT INTO comments (thread_id, username, content) VALUES (?, ?, ?)', (thread_id, username, content))
        con.commit()

    creator = cur.execute('SELECT creator FROM threads WHERE id = ?', (thread_id,)).fetchone()
    thread = cur.execute('SELECT * FROM threads WHERE id = ?', (thread_id,)).fetchone()
    comments = cur.execute('SELECT * FROM comments WHERE thread_id = ?', (thread_id,)).fetchall()
    
    commUsername = comments[0][2]

    commentPic = curLog.execute('SELECT userPic FROM login WHERE username = ?', (commUsername,)).fetchall()
    userPic = curLog.execute('SELECT userPic FROM login WHERE username = ?', (creator)).fetchone()
    
    clean_url = re.sub(r"[()',]", "", str(userPic))
    clean_url_com = re.sub(r"[()',]", "", str(commentPic[0]))
    conLog.close()
    con.close()

    return render_template('thread-template.html', thread=thread, comments=comments, userPic=clean_url, commentPic=clean_url_com)

@app.route('/user/<string:username>', methods=['GET', 'POST'])
def displayUserPage(username):
    con = sqlite3.connect(login_db)
    cur = con.cursor()
    userPic = cur.execute('SELECT userPic FROM login WHERE username = ?', (username)).fetchone()
    bio = cur.execute('SELECT bio FROM login WHERE username = ?', (username)).fetchone()
    threads = cur.execute('SELECT title, timestamp FROM threads WHERE username = ?', (username)).fetchone()
    
    con.close()

    return render_template("userPage.html", username=username, userPic=userPic, bio=bio, threads=threads)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
