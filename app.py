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

    titleAndDescription = genai_response_obj
    

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
    

    genai_response = global_client.models.generate_content(
      model="gemini-2.0-flash",
      contents=f"""
You are used in an api for a learning platform, please generate some json data.
The user wants to learn: [{titleAndDescription.get("title")}] - [{titleAndDescription.get("description")}]
These are some notes the user inputed: [{data.get("notes")}]
Please responde with some notes you noticed based on the user input, these notes will or can improve the learning ways and make the ai know more about the user.
Responde with the following strict schema example on python:

[
  {{
    "note": "The user loves scratch, we might use his past scratch knowlege to make python learning easier.",
    "id": 1
  }},
  {{
    "note": "The user is named Mohamed and he is 8 years old, we might simplify the teaching to fit his age and give examples from daily life.",
    "id": 2
  }},
  ...
]
""",
      config={
        'response_mime_type': 'application/json',
      }
    )

    genai_response_obj = json.loads(genai_response.text)

    for note in genai_response_obj:
      with connection:
        with connection.cursor() as cursor:
          cursor.execute(
            """
INSERT INTO "note" (course,content) VALUES (%s,%s);
""",(course_id, note.get("note"))
          )

    return "", 202
  

@app.route("/chat/send/<int:courseID>/<int:planItemID>",methods=["GET"])
def sendToChat(courseID,planItemID):
  data = request.get_json()

  with connection:
    with  connection.cursor() as cursor:
      cursor.execute('SELECT id,content FROM "note" where course = %s;',(courseID,))
      rows = cursor.fetchall()
      notes_str = "Notes:\n"
      for row in rows:
        notes_str += f"{row[0]}- {row[1]}\n"
      print(notes_str)

  with connection:
    with  connection.cursor() as cursor:
      cursor.execute('SELECT title FROM "course" where id = %s;',(courseID,))
      courseTitle = cursor.fetchone()

  with connection:
    with  connection.cursor() as cursor:
      cursor.execute('SELECT content FROM "planItem" where id = %s AND course = %s;',(planItemID,courseID))
      lesson = cursor.fetchone()

  with connection:
    with  connection.cursor() as cursor:
      cursor.execute("""
SELECT id, content, ai
FROM "message"
WHERE "message"."planitem" = %s AND "message"."course" = %s;
""",(planItemID,courseID))
      rows = cursor.fetchall()
      history = [

      ]
      for row in rows:
        history.append(
          {
            "id": row[0],
            "content": row[1],
            "sender": "user" if row[2] == False else "AI"
          },
        )






  ai_client = genai.Client(api_key=GENAI_API)
  genai_response = ai_client.models.generate_content(model="gemini-2.0-flash",contents=f"""
You are user in an api of a ai course learning platform.
Here is some notes about the user that you should use to improve there learning experiences:
{notes_str}
---
You should teach the user this lesson and This lesson is part of this course:
{courseTitle}
And todays lesson is:
{lesson}
Start by explain the lesson with great detail (if not already done) and ansower any qustions the user gives you.
---
Here is the history (if there):
{json.dumps(history)}
---
Now the user typed:
{data.get("message")}
---
Respond with the following strict scheema in json:
{{
  "response": "Your markdown fully formated response here"
}}
""",config={
  'response_mime_type': 'application/json',
})
  
  obj_genai_response = json.loads(genai_response.text)


  with connection:
    with connection.cursor() as cursor:
      cursor.execute("""
INSERT INTO "message" (course,planitem,content,ai) VALUES (
  %s,%s,%s,%s
)
""",(courseID,planItemID,data.get("message"),False)
      )

  with connection:
      with connection.cursor() as cursor:
        cursor.execute("""
  INSERT INTO "message" (course,planitem,content,ai) VALUES (
    %s,%s,%s,%s
  )
  """,(courseID,planItemID,obj_genai_response.get("response"),True)
        )


  return jsonify({"response": obj_genai_response.get("response")}),200