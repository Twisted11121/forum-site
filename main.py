from flask import Flask, render_template, request, session, jsonify, redirect, url_for, send_from_directory
import sqlite3
from datetime import datetime
import re
import requests
import os

app = Flask(__name__)
database = 'threads.db'
login_db = 'login.db'
request_db = 'request.db'

def requastDB():
    con_login = sqlite3.connect(login_db)
    cur_login = con_login.cursor()
    cur_login.execute('''
        CREATE TABLE IF NOT EXISTS fRequests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        content TEXT NOT NULL)''')
    
    con_login.commit()
    con_login.close()    

requastDB()

def i_login_db():
    con_login = sqlite3.connect(login_db)
    cur_login = con_login.cursor()
    cur_login.execute('''
                      CREATE TABLE IF NOT EXISTS login (
                        username TEXT,
                        password TEXT,
                        userPic TEXT,
                        bio TEXT
                      )''')
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
        return render_template('index.html', username=session['username'])

    return render_template('login_page.html')

@app.route('/displayThreads')
def displayThreads():
    con = sqlite3.connect(database)
    cur = con.cursor()
    threads = cur.execute('SELECT * FROM threads').fetchall()
    con.close()
    
    username = session['username']
    

    return render_template('threads.html', threads=threads, username=username)

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
    
    defaultUserPic = "default-avatar.jpg"
    bio = "Hello, I'm new here! :)"

    cur_login.execute("INSERT INTO login (username, password, userPic, bio) VALUES (?, ?, ?, ?)", (username, password, defaultUserPic, bio))
    con_login.commit()
    con_login.close()
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template("login_page.html")


@app.route('/userPictures/<path:filename>')
def user_pictures(filename):
    return send_from_directory('userPictures', filename)


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
    userPic = curLog.execute('SELECT userPic FROM login WHERE username = ?', (creator)).fetchone()
    clean_url = re.sub(r"[()',]", "", str(userPic))
    
    if comments:
        commUsername = comments[0][2]
        commentPic = curLog.execute('SELECT userPic FROM login WHERE username = ?', (commUsername,)).fetchall()
        clean_url_com = re.sub(r"[()',]", "", str(commentPic[0]))
        conLog.close()
        con.close()
        return render_template('thread-template.html', thread=thread, comments=comments, userPic=clean_url, commentPic=clean_url_com)

    conLog.close()
    con.close()

    return render_template('thread-template.html', thread=thread, userPic=clean_url)

@app.route('/user/<username>', methods=['GET', 'POST'])
def displayUserPage(username):
    con = sqlite3.connect(login_db)
    cur = con.cursor()
    con_T = sqlite3.connect(database)
    cur_T = con_T.cursor()

    userPic = cur.execute('SELECT userPic FROM login WHERE username = ?', (username,)).fetchone()
    bio = cur.execute('SELECT bio FROM login WHERE username = ?', (username,)).fetchone()
    threads = cur_T.execute('SELECT id, title, timestamp FROM threads WHERE creator = ?', (username,)).fetchall()
    
    clean_userPic = re.sub(r"[()',]", "", str(userPic))
    clean_bio = re.sub(r"[()',]", "", str(bio))
    
    con.close()
    con_T.close()
    
    return render_template("userPage.html", 
                         username=username, 
                         userPic=clean_userPic, 
                         bio=clean_bio, 
                         threads=threads)


@app.route('/editPage', methods=['GET'])
def editPage():
    Username = request.args.get('username')
    if session["username"] ==  Username:
        return jsonify({'success': True})

@app.route("/editProfile", methods=['GET'])
def editProfile():
    con = sqlite3.connect(login_db)
    cur = con.cursor()
    username = session['username']
    bio = cur.execute('SELECT bio FROM login WHERE username = ?', (username,)).fetchone()
    clean_bio = re.sub(r"[()',]", "", str(bio))
    return render_template('updateProfile.html', username=session['username'], prevbio=bio)


@app.route('/updateProfile', methods=['POST'])
def updateProfile():
    con = sqlite3.connect(login_db)
    cur = con.cursor()

    username = session['username']
    bio = request.form.get('bio', None)
    userPic = request.files.get('profilePic', None)

    if bio or userPic:
        if userPic:
            file_path = os.path.join("userPictures", userPic.filename)
            userPic.save(file_path)
            cur.execute('UPDATE login SET userPic = ? WHERE username = ?', (userPic.filename, username))
        
        if bio:
            cur.execute('UPDATE login SET bio = ? WHERE username = ?', (bio, username))
        
        con.commit()

    con.close()

    return redirect(url_for('displayUserPage', username=username))



@app.route('/novice')
def novice():
    
    if request.method == 'POST':
        con = sqlite3.connect(request_db)
        cur = con.cursor()

        content = request.form['content']
        username = session['username']  

        cur.execute('INSERT INTO fRequests (username, content) VALUES (?, ?, ?)', (username, content))
        con.commit()
        con.close()
        return redirect(url_for('displayRequests'))
        
    
    return render_template('novice.html')

@app.route('/cuteCat')
def getCat():
    img_url = requests.get("https://cataas.com/cat?json=true").json()
    image=f"https://cataas.com/cat/{img_url["id"]}"
    
    return render_template('cuteCat.html', img=image)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    print(query)
    if not query:
        query = ""
    con = sqlite3.connect(database)
    cur = con.cursor()
    
    threads = cur.execute("SELECT * FROM threads WHERE title LIKE ?", ('%' + query + '%',)).fetchall()
    
    con.close()
    
    return render_template('search.html', threads=threads, query=query)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
