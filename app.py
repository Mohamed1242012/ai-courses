from flask import Flask
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

app = Flask(__name__)
url = os.getenv("POSTGRESQL_URL")
connection = psycopg2.connect(url)

with connection:
  with connection.cursor() as cursor:
    cursor.execute("""
                   
CREATE TABLE IF NOT EXISTS "course" (
	id SERIAL PRIMARY KEY,
  title VARCHAR(255),
  description VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS "planItem" (
	id SERIAL PRIMARY KEY,
  course INTEGER REFERENCES "course"(id),
  content TEXT
);

CREATE TABLE IF NOT EXISTS "note" (
	id SERIAL PRIMARY KEY,
  course INTEGER REFERENCES "course"(id),
  content TEXT
);

CREATE TABLE IF NOT EXISTS "message" (
	id SERIAL PRIMARY KEY,
  course INTEGER REFERENCES "course"(id),
  planItem INTEGER REFERENCES "planItem"(id),
  content TEXT,
  ai BOOLEAN
);

""")

@app.route("/")
def home():
  return "Hello World"