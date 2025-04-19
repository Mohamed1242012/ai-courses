from flask import Flask, request, Response, jsonify
import os
from dotenv import load_dotenv
import psycopg2
from google import genai # Use gemeni api with this
import json

load_dotenv()

app = Flask(__name__)
DB_URL = os.getenv("POSTGRESQL_URL")
GENAI_API = os.getenv("GENAI_API")
connection = psycopg2.connect(DB_URL)
global_client = genai.Client(api_key=GENAI_API)

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

@app.route("/api/course",methods=["POST","DELETE","PATCH"])
def home():
  data = request.get_json()
  # Sample data we get from client
  {
    "learn": "Python",
    "notes": "I have some scratch experience."
  }

  if request.method == "POST": # POST for create
    genai_response = global_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"""
You are used in an api for a learning platform, please generate some json data.
You will get now the user input in two text boxes,
The user wants to learn: [{data.get("learn")}]
Please generate a small title and description of what the user needs to learn, your data will be used to create an entety in a database.
Responde with the following schema example:
{{
  "title": "Python",
  "description": "Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation."
}}
""",
        config={
          'response_mime_type': 'application/json',
        }
    )
    genai_response_obj = json.loads(genai_response.text)
    with connection:
      with connection.cursor() as cursor:
        cursor.execute("""
INSERT INTO "course" (title,description) VALUES
	(
  	%s,
    %s
  ) RETURNING id;
""",(genai_response_obj.get("title"),genai_response_obj.get("description")))
        course_id = cursor.fetchone()[0]
    

    genai_response = global_client.models.generate_content(
      model="gemini-2.0-flash",
      contents=f"""
You are used in an api for a learning platform, please generate some json data.
The user wants to learn: [{genai_response_obj.get("title")}] - [{genai_response_obj.get("description")}]
These are some notes the user inputed, use these notes to make a plan that fits his age and learning style: [{data.get("notes")}]
Please generate a full plan for the user to learn, this plan will always contain in the biggening "general" then lessons of the thing the user wants to learn, your data will be used to create an entety in a database.
Responde with the following strict schema example with only topic and id:
[
  {{
    "topic": "General",
    "id": 1
  }},
  {{
    "topic": "What is Python",
    "id": 2
  }},
  {{
    "topic": "Using Variables",
    "id": 3
  }},
  ...
]
""",
      config={
        'response_mime_type': 'application/json',
      }
    )

    genai_response_obj = json.loads(genai_response.text)

    for planItem in genai_response_obj:
      with connection:
        with connection.cursor() as cursor:
          cursor.execute(
            """
INSERT INTO "planItem" (course,content) VALUES (%s,%s);
""",(course_id, planItem.get("topic"))
          )

          # now notes then start working on convo
    




    return "", 202