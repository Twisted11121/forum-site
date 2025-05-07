from flask import Flask, render_template, request, session, jsonify, redirect, url_for, send_from_directory
import sqlite3
from datetime import datetime
import re
import requests
import os
from urllib.parse import quote


app = Flask(__name__)
database = 'threads.db'
login_db = 'login.db'
request_db = 'request.db'

def requastDB():
    con = sqlite3.connect(database)
    cur = con.cursor()
    con.execute('''
        CREATE TABLE IF NOT EXISTS fRequests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL)''')
    
    con.commit()
    con.close()    

requastDB()

def i_login_db():
    con_login = sqlite3.connect(login_db)
    cur_login = con_login.cursor()
    cur_login.execute('''
                      CREATE TABLE IF NOT EXISTS login (
                        username TEXT,
                        password TEXT,
                        userPic TEXT,
                        bio TEXT,
                        role TEXT DEFAULT 'user'
                      )''')
    
    """cur_login.execute('''
                      INSERT INTO login 
                      (username, password, userPic, bio)
                      VALUES (?, ?, ?, ?)''',
                      ("admin", "admin", "default-avatar.jpg", "Hello, I'm admin! :)"))"""
    
    con_login.commit()
    con_login.close()

def thread_db():
    con = sqlite3.connect(database)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY,
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
    
    #cur.execute('DROP TABLE IF EXISTS testi')
    #cur.execute('DROP TABLE IF EXISTS test_comments')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS testi (
            id INTEGER PRIMARY KEY,
            predmet TEXT NOT NULL,
            letnik INTEGER NOT NULL, 
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            creator TEXT NOT NULL,
            timestamp TIME NOT NULL,
            testPic TEXT
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS test_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (test_id) REFERENCES testi (id) ON DELETE CASCADE
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
    threads1 = cur.execute('SELECT count(*) FROM threads').fetchall()
    threads = cur.execute('SELECT * FROM threads').fetchall()
    comments = []
    for x in range(0, threads1[0][0]):
        comments.append(cur.execute('SELECT count(*) FROM comments WHERE thread_id = ?', (threads[x][0],)).fetchall())
    con.close()
    
    username = session['username']
    

    return render_template('threads.html', threads=threads, username=username, comments=comments, type="threads")

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
        commentPics = {}
        for comment in comments:
            commUsername = comment[2]
            commentPic = curLog.execute('SELECT userPic FROM login WHERE username = ?', (commUsername,)).fetchone()
            clean_url_com = re.sub(r"[()',]", "", str(commentPic)) if commentPic else "default-avatar.jpg"
            commentPics[commUsername] = clean_url_com
        conLog.close()
        con.close()
        return render_template('thread-template.html', thread=thread, comments=comments, userPic=clean_url, commentPics=commentPics, loggedInUser=session['username'])

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
    test = cur_T.execute('SELECT id, title, timestamp FROM testi WHERE creator = ?', (username,)).fetchall()
    
    clean_userPic = re.sub(r"[()',]", "", str(userPic))
    clean_bio = re.sub(r"[()',]", "", str(bio))
    
    con.close()
    con_T.close()
    
    return render_template("userPage.html", 
                         username=username, 
                         userPic=clean_userPic, 
                         bio=clean_bio, 
                         threads=threads,
                         tests=test)


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
    return render_template('updateProfile.html', username=session['username'], prevbio=clean_bio)


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
        
    
    return render_template('novice.html', username=session['username'])

@app.route('/cuteCat')
def getCat():
    img_url = requests.get("https://cataas.com/cat?json=true").json()
    image=f"https://cataas.com/cat/{img_url["id"]}"
    
    return render_template('cuteCat.html', img=image, username=session['username'])


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        query = ""
    con = sqlite3.connect(database)
    cur = con.cursor()
    
    threads = cur.execute("SELECT * FROM threads WHERE title LIKE ?", ('%' + query + '%',)).fetchall()
    
    con.close()
    
    return render_template('search.html', threads=threads, query=query, username=session['username'])


@app.route('/requestFeature', methods=['POST'])
def storeRequest():
    con = sqlite3.connect(database)
    cur = con.cursor()
    
    username = session['username']
    title = request.form['featureTitle']
    content = request.form['featureDescription']
    
    cur.execute('INSERT INTO fRequests (username, title, content) VALUES (?, ?, ?)', (username, title, content))
    con.commit()
    con.close()
    return render_template('novice.html', username=session['username'])

@app.route('/adminDashboard', methods=['GET'])
def adminDashboard():
    con = sqlite3.connect(login_db)
    cur = con.cursor()
    
    username = session['username']
    role = cur.execute('SELECT role FROM login WHERE username = ?', (username,)).fetchone()
    
    if role or role[0] == 'admin':
        return render_template('adminDashboard.html', username=session['username'])
    else:
        return render_template('index.html')

@app.route('/users', methods=['GET'])
def users():
    con = sqlite3.connect(login_db)
    cur = con.cursor()
    
    if session['username'] == 'admin':
           
        users = cur.execute('SELECT username, userPic FROM login').fetchall()
        
        users = [(user[0], user[1]) for user in users]    
        return render_template('users.html', users=users, username=session['username'])
    
    
    con.close()    
    return render_template('index.html')

@app.route('/deleteUser', methods=['POST'])
def deleteUser():
    con = sqlite3.connect(login_db)
    cur = con.cursor()
    
    username = request.form['username']
    
    cur.execute('DELETE FROM login WHERE username = ?', (username,))
    con.commit()
    con.close()
    
    return redirect(url_for('users'))


@app.route('/displayRequests')
def displayRequests():
    con = sqlite3.connect(database)
    cur = con.cursor()
    
    requests = cur.execute('SELECT * FROM fRequests').fetchall()
    con.close()
    
    return render_template('feauture-requests.html', requests=requests, username=session['username'])

@app.route('/completedReqeuest', methods=['POST'])
def completedRequest():
    con = sqlite3.connect(database)
    cur = con.cursor()
    
    request_id = request.form['id']
    
    cur.execute('DELETE FROM fRequests WHERE id = ?', (request_id,))
    con.commit()
    con.close()
    
    return redirect(url_for('displayRequests'))


@app.route('/deleteThread', methods=['GET', 'POST'])
def deleteThread():
    
    if request.method == 'GET':
        creator = request.args.get('creator')
        if session['username'] == creator:
            return jsonify({'success': True, 'creator': creator})
        else:
            return jsonify({'error': False, 'creator': creator})
        
    
    if request.method == 'POST':
        con = sqlite3.connect(database)
        cur = con.cursor()
        
        thread_id = request.form.get('threadId')
        
        cur.execute('DELETE FROM threads WHERE id = ?', (thread_id,))
        cur.execute('DELETE FROM comments WHERE thread_id = ?', (thread_id,))
        con.commit()
        cur.execute('''
            UPDATE threads
            SET id = id - 1
            WHERE id > ?
        ''', (thread_id,))
        
        con.commit()
        con.close()
        
        return redirect(url_for('index'))


@app.route('/testPics/<path:filename>')
def test_pictures(filename):
    return send_from_directory('testPic', filename)


@app.route('/testi')
def test1():
    con = sqlite3.connect(database)
    cur = con.cursor()
    
    threads = cur.execute('SELECT * FROM testi').fetchall()
    username = session['username']
    threads1 = cur.execute('SELECT count(*) FROM testi').fetchall()

    
    comments = []
    for x in range(0, threads1[0][0]):
        comments.append(cur.execute('SELECT count(*) FROM comments WHERE thread_id = ?', (threads[x][0],)).fetchall())
    con.close()
    
    username = session['username']

    return render_template('show-tests.html', username=username, comments=comments, threads=threads, type="testi")

@app.route('/create_testi', methods=['GET', 'POST'])
def create_testi():
    if request.method == 'POST':
        predmet = request.form.get('predmet', None)
        letnik = request.form.get('letnik', 1)
        title = request.form['title']
        content = request.form['content']
        username = session['username']
        now1 = datetime.now()
        formatted_date_time = now1.strftime("%d/%m/%Y %H:%M")
        testPic = request.files.get('test')
        directory = 'testPic'
        if not os.path.exists(directory):
            os.makedirs(directory)

        filename = None
        if testPic and testPic.filename != '':
            formatted_filename = re.sub(r'\s+', '_', testPic.filename)
            formatted_filename = re.sub(r'[^\w\.-]', '', formatted_filename)
            file_path = os.path.join("testPic", formatted_filename)
            testPic.save(file_path)
            filename = formatted_filename
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute('INSERT INTO testi (predmet, letnik, title, content, creator, timestamp, testPic) VALUES (?, ?, ?, ?, ?, ?, ?)', (predmet, letnik, title, content, username, formatted_date_time, filename))
        con.commit()
        con.close()
        
        return redirect(url_for('test1'))

    return render_template('create_thread.html', type="testi")

@app.route('/testi/<int:test_id>', methods=['GET', 'POST'])
def testi(test_id):
    con = sqlite3.connect(database)
    cur = con.cursor()
    conLog = sqlite3.connect(login_db)
    curLog = conLog.cursor()

    if request.method == 'POST':
        content = request.form['content']
        username = session['username']  

        cur.execute('INSERT INTO comments (thread_id, username, content) VALUES (?, ?, ?)', (test_id, username, content))
        con.commit()

    creator = cur.execute('SELECT creator FROM testi WHERE id = ?', (test_id,)).fetchone()
    thread = cur.execute('SELECT * FROM testi WHERE id = ?', (test_id,)).fetchone()
    comments = cur.execute('SELECT * FROM test_comments WHERE test_id = ?', (test_id,)).fetchall()
    userPic = curLog.execute('SELECT userPic FROM login WHERE username = ?', (creator)).fetchone()
    clean_url = re.sub(r"[()',]", "", str(userPic))
    if comments:
        commentPics = {}
        for comment in comments:
            commUsername = comment[2]
            commentPic = curLog.execute('SELECT userPic FROM login WHERE username = ?', (commUsername,)).fetchone()
            clean_url_com = re.sub(r"[()',]", "", str(commentPic)) if commentPic else "default-avatar.jpg"
            commentPics[commUsername] = clean_url_com
        conLog.close()
        con.close()
        return render_template('thread-template.html', thread=thread, comments=comments, userPic=clean_url, commentPics=commentPics, loggedInUser=session['username'])

    conLog.close()
    con.close()
    print(thread[7])
    return render_template('test-template.html', thread=thread, userPic=clean_url)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
