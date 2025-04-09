from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import sqlite3
import datetime
import requests

app = Flask(__name__)
database = 'threads.db'
login_db = 'login.db'
request_db = 'request.db'

def loginDB():
    con_login = sqlite3.connect(login_db)
    cur_login = con_login.cursor()
    cur_login.execute("CREATE TABLE IF NOT EXISTS login(username TEXT, password TEXT)")
    con_login.commit()
    con_login.close()

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


def threadDB():
    con = sqlite3.connect(database)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME
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

requastDB()
loginDB()
threadDB()

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
    
    cur_login.execute("INSERT INTO login (username, password) VALUES (?, ?)", (username, password))
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
        
        con = sqlite3.connect(database)
        cur = con.cursor()
        time = datetime.datetime.now().strftime("%d.%m.%Y at %H:%M")
        cur.execute('INSERT INTO threads (title, content, timestamp) VALUES (?, ?, ?)', (title, content, time))
        con.commit()
        con.close()
        
        return redirect(url_for('displayThreads'))
    return render_template('create_thread.html')

@app.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
def thread(thread_id):
    con = sqlite3.connect(database)
    cur = con.cursor()

    if request.method == 'POST':
        content = request.form['content']
        username = session['username']  

        cur.execute('INSERT INTO comments (thread_id, username, content) VALUES (?, ?, ?)', (thread_id, username, content))
        con.commit()

    thread = cur.execute('SELECT * FROM threads WHERE id = ?', (thread_id,)).fetchone()
    comments = cur.execute('SELECT * FROM comments WHERE thread_id = ?', (thread_id,)).fetchall()
    con.close()

    if thread is None:
        return "Thread not found", 404

    return render_template('thread-template.html', thread=thread, comments=comments)


def displayThreads():
    con = sqlite3.connect(request_db)
    cur = con.cursor()
    threads = cur.execute('SELECT * FROM threads').fetchall()
    con.close()
    
    #Finish feature-requests.html
    return render_template('threads.html', threads=threads) 


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

if __name__ == "__main__":
    app.run(debug=True)
