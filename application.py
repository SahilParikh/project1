import os, json
import requests
import hashlib
import psycopg2

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#Configure Tables | At the start of each run, it drops the tables previously created to prevent 'table already exists' errors
#db.execute('DROP TABLE users')
#db.execute("CREATE TABLE users(id SERIAL PRIMARY KEY, name VARCHAR, password VARCHAR)")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("name")
    password = request.form.get("password")
    hash_pwd = hashlib.sha256(password.encode('utf-8')). hexdigest()
             
    if name != '':
        if request.form['submit_button'] == 'Sign Up':
            info = db.execute("SELECT name FROM users where name=:name", {'name': name}).fetchone() 

            if info != None:
                return render_template('account_exists.html')
            
            else:
                db.execute("INSERT INTO users (name, password) VALUES (:name, :password)", {'name': name, 'password': hash_pwd})
                db.commit()
                
                user_id = db.execute("SELECT id FROM users where name=:name", {'name': name}).fetchone()
                
                for i in user_id:
                    session["user_name"] = i.name
                    session["user_id"] = i.id              
                
                return render_template('registration.html')          

        if request.form['submit_button'] == 'Login':
            user = db.execute("SELECT * FROM users WHERE (name = :name AND password = :password)", {'name': name, 'password': hash_pwd}).fetchall()
            
            for i in user:
                if i.name == name and i.password == hash_pwd:
                    session['user_name'] = i.name
                    return redirect(url_for('search'))         
            else:
                return redirect(url_for('index'))

    else:
        return render_template('index.html')
    

@app.route("/search", methods = ['POST', 'GET'])
def search():
    return render_template("search.html")
    
@app.route('/results', methods=['POST'])
def results():
    item = (request.form.get("name")).title() 


    if request.form['submit_button'] == 'Search' and item:
        rows = db.execute("SELECT * FROM books WHERE books.isbn LIKE '%{0}%' OR books.title LIKE '%{0}%' OR books.author LIKE '%{0}%' or books.year LIKE '%{0}%'".format(item)).fetchall()
        if rows != None:
            return render_template('results.html', rows = rows)
        else:
            return render_template('results.html')
    else:
        return render_template('search.html')

   
  

@app.route('/book/<title>/<isbn>/<author>/<year>', methods = ["POST", "GET"])
def book(title, isbn, author, year):
    book_res = [title, isbn, author, year]
    error = 'No Review Entered'
    rating = (requests.get("https://www.goodreads.com/book/review_counts.json", params = {'key': 'ywiShb8nqSAlncAaP6bVKQ', 'isbns': isbn})).json()
    avg_rating = rating["books"][0]["average_rating"]
    total_ratings = rating["books"][0]["reviews_count"]
    username = session["user_name"]
    stars = request.form.get('stars')

    if session.get('message') is None:
        session['message'] = []

    if request.method == "POST":
        review = request.form.get('name')
        

        if review != '':
            review_check = db.execute("SELECT * from reviews WHERE (username = :username AND book = :book)", {'username': username, 'book': title}).fetchone()

            if review_check == None:               
                db.execute("INSERT INTO reviews(username, book, review) VALUES (:username, :book, :review)", {'username': username, 'book': title, 'review': review})               
                db.commit()
                
                session['message'].append(review)

                return render_template('book.html', book_res= book_res, username = username, message = session['message'], stars = stars, rating = avg_rating, total_ratings = total_ratings)
            else:
                return render_template('book.html', book_res= book_res, username = username, message = session['message'], stars = stars, error = 'Book already rated by user', rating = avg_rating, total_ratings = total_ratings)

    return render_template('book.html', book_res = book_res, username = username, message = session['message'], stars = stars, rating = avg_rating, total_ratings = total_ratings)


@app.route('/api/<isbn>')
def api(isbn):
    book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn': isbn}).fetchall()
    
    if book_info:
        isbn_res = (requests.get("https://www.goodreads.com/book/review_counts.json", params = {'key': 'ywiShb8nqSAlncAaP6bVKQ', 'isbns': isbn})).json()
        
        for i in book_info:
            title = i.title
            author = i.author
            year = i.year
    
        return jsonify({
            "title": title, 
            "author": author,
            "year": year, 
            "isbn": isbn,
            "review_count": isbn_res["books"][0]["reviews_count"],
            "average_score": isbn_res["books"][0]["average_rating"]})
    else:
        return 'Error 404 ISBN Not Found'

@app.route('/logout')
def logout():
    session.clear()
    return render_template('index.html')
