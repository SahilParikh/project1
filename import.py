import csv
import os
import psycopg2

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

#engine = create_engine("postgres://lvuweiqfwjsijf:23d8dd45cc95928fa1b49957b18966ccf6a3567b6ccbb6eee7cbe97968388586@ec2-54-86-170-8.compute-1.amazonaws.com:5432/dcm0dr7j9dm58")
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



# Simpler Version 
def main():
    db.execute('DROP TABLE authors')
    db.execute('DROP TABLE years')
    db.execute('DROP TABLE books')

    f = open("books.csv")
    reader = csv.reader(f)
    next(reader, None) #skips the header row

    db.execute("CREATE TABLE books(id SERIAL PRIMARY KEY, isbn VARCHAR, title VARCHAR, author VARCHAR, year VARCHAR)")

    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books(isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {'isbn': isbn, 'title': title, 'author': author, 'year': year})
    
    db.commit() 

# The code below generates 3 tables (1 for authors, 1 for the years, and 1 containing ISBN, Title, author_id, year_id)
# The third and fourth column in the 3rd table reference the id # for the author and year, respectively, from their respective tables. 
# This code can be uncommented and ran, it will run just fine. However, for the purposes of using this project, I created a simpler version above
'''def main():
    db.execute('DROP TABLE authors') #incase you have predefined tables with the same name
    db.execute('DROP TABLE years')
    db.execute('DROP TABLE books')

    f = open("books.csv")
    reader = csv.reader(f)
    next(reader, None) #skips the header row
    
    author_dict = {} # blank dicctionary to store information
    years_dict = {}

    author_counter = 1 #initial counters
    year_counter = 1

    db.execute("CREATE TABLE authors(id SERIAL PRIMARY KEY, name VARCHAR NOT NULL UNIQUE)") #create each table 
    db.execute("CREATE TABLE years(id SERIAL PRIMARY KEY, year_written int UNIQUE)")
    db.execute("CREATE TABLE books(id SERIAL PRIMARY KEY, isbn VARCHAR, title VARCHAR, author_id INT, year_id INT)")

    for isbn, title, author, year in reader:

        if author not in author_dict:
            db.execute("INSERT INTO authors (name) VALUES (:name)", {"name": author})
            author_dict[author] = author_counter
            author_counter += 1

        if year not in years_dict:
            db.execute("INSERT INTO years(year_written) VALUES (:year_written)",{'year_written': year})
            years_dict[year] = year_counter
            year_counter += 1

        db.execute("INSERT INTO books(isbn, title, author_id, year_id) VALUES (:isbn, :title, :author_id, :year_id)", {'isbn': isbn, 'title': title, 
        'author_id': author_dict[author], 'year_id': years_dict[year]})


        # Joins tables authors, years with table books | due to the 10k row limit on Heroku, I wasn't able to create another table  
        #db.execute("SELECT isbn, title, name, year_written FROM books INNER JOIN authors on authors.id = books.author_id INNER JOIN years on years.id = books.year_id")   

    db.commit() 
'''
if __name__ == "__main__":
    main()