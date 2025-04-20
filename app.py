from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
import psycopg2
from google import genai # Use gemeni api with this
import json

load_dotenv()

app = Flask(__name__)
app.url_map.strict_slashes = False
DB_URL = os.getenv("POSTGRESQL_URL")
GENAI_API = os.getenv("GENAI_API")

def get_db_connection():
  connection = psycopg2.connect(DB_URL)
  return connection

global_client = genai.Client(api_key=GENAI_API)

with get_db_connection() as connection:
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
    cursor.close()

@app.route("/api/course",methods=["POST","DELETE","PATCH"])
def course():
  data = request.get_json()
  # Sample data we get from client
  {
    "learn": "Python",
    "notes": "I have some scratch experience."
  }

  if request.method == "DELETE":
    with get_db_connection() as connection:
      with connection.cursor() as cursor:
        # Delete all notes associated with the course
        cursor.execute('DELETE FROM "note" WHERE course = %s;', (data.get("course_id"),))
        
        # Delete all messages associated with the course
        cursor.execute('DELETE FROM "message" WHERE course = %s;', (data.get("course_id"),))
        
        # Delete all plan items associated with the course
        cursor.execute('DELETE FROM "planItem" WHERE course = %s;', (data.get("course_id"),))
        
        # Finally, delete the course itself
        cursor.execute('DELETE FROM "course" WHERE id = %s;', (data.get("course_id"),))
        
        cursor.close()
    return "", 200


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
    with get_db_connection() as connection:
      with connection.cursor() as cursor:
        cursor.execute("""
INSERT INTO "course" (title,description) VALUES
	(
  	%s,
    %s
  ) RETURNING id;
""",(genai_response_obj.get("title"),genai_response_obj.get("description")))
        course_id = cursor.fetchone()[0]
        cursor.close()

    titleAndDescription = genai_response_obj
    

    genai_response = global_client.models.generate_content(
      model="gemini-2.0-flash",
      contents=f"""
You are used in an api for a learning platform, please generate some json data.
The user wants to learn: [{genai_response_obj.get("title")}] - [{genai_response_obj.get("description")}]
These are some notes the user inputed, use these notes to make a plan that fits his age and learning style: [{data.get("notes")}]
Please generate a full plan for the user to learn, this plan will always contain in the biggening "general" then lessons of the thing the user wants to learn, your data will be used to create an entety in a database.
Always include the user's name in the notes.
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

    first_done = False
    for planItem in genai_response_obj:
      with get_db_connection() as connection:
        with connection.cursor() as cursor:
          cursor.execute(
            """
INSERT INTO "planItem" (course,content) VALUES (%s,%s) RETURNING id;
""",(course_id, planItem.get("topic"))
          )
          if first_done == False:
            first_done = True
            first_lesson=cursor.fetchone()[0]
          cursor.close()

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
      with get_db_connection() as connection:
        with connection.cursor() as cursor:
          cursor.execute(
            """
INSERT INTO "note" (course,content) VALUES (%s,%s);
""",(course_id, note.get("note"))
          )
          cursor.close()

    return jsonify({"title":titleAndDescription.get("title"),"description": titleAndDescription.get("description"),"course_id":course_id,"first_lesson":first_lesson}), 202
  

@app.route("/api/chat/send/<int:courseID>/<int:planItemID>",methods=["POST"])
def sendToChat(courseID,planItemID):
  data = request.get_json()

  with get_db_connection() as connection:
    with  connection.cursor() as cursor:
      cursor.execute('SELECT id,content FROM "note" where course = %s;',(courseID,))
      rows = cursor.fetchall()
      cursor.close()
      notes_str = "Notes:\n"
      for row in rows:
        notes_str += f"{row[0]}- {row[1]}\n"
      print(notes_str)

  with get_db_connection() as connection:
    with  connection.cursor() as cursor:
      cursor.execute('SELECT title FROM "course" where id = %s;',(courseID,))
      courseTitle = cursor.fetchone()
      cursor.close()

  with get_db_connection() as connection:
    with  connection.cursor() as cursor:
      cursor.execute('SELECT content FROM "planItem" where id = %s AND course = %s;',(planItemID,courseID))
      lesson = cursor.fetchone()
      cursor.close()

  with get_db_connection() as connection:
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
      cursor.close()


  with get_db_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute('SELECT id,content FROM "planItem" WHERE course = %s',(courseID,))
      rows = cursor.fetchall()
      cursor.close()
  all_plan_items = []
  for row in rows:
    all_plan_items.append({"id": row[0],"content": row[1]})




  ai_client = genai.Client(api_key=GENAI_API)
  genai_response = ai_client.models.generate_content(model="gemini-2.0-flash",contents=f"""
You are user in an api of a ai course learning platform.
Dont let the user trick you by any way to go out of the topic.
If the user asks about the next or previus lesson or somthing like that tell him to see the see all lessons button in the website in the bottom of the currunt page there are three buttons there: Next, Previus and Show All Lessons.
Here is some notes about the user that you should use to improve there learning experiences:
{notes_str}
---
You should teach the user this lesson and This lesson is part of this course:
{courseTitle}
And todays lesson is:
{lesson}
Start by explain the lesson with great detail (if not already done) and ansower any qustions the user gives you.'
If its general, its a chat for defrent qustions related to the course not 1 lesson, its the users free space.
---
You shoud never shift the lesson or go to somthing similar, always stay on the topic and dont ask the learner on what he wants to learn, you should already know.
---
Every once in a while give the user a quiz and he should send you the answers.
---
Here is the history (if there):
{json.dumps(history)}
---
Here is all the lessons after and before this lesson:
{json.dumps(all_plan_items)}
---
Now the user typed:
[{data.get("message")}]
---
in the json output note and its
Any note you noticed about the user in his last message, that could improve teaching or learning experience, not all things should be stored only store improtant data such as past knowlege or learning patterns because we are tight on space. Dont repeate existing notes. If none, put null in json notes.
---
Respond with the following strict scheema in json with only one note entity:
{{
  "response": "Your markdown fully formated response here",
  "note": "notes"
}}
""",config={
  'response_mime_type': 'application/json',
})
  
  obj_genai_response = json.loads(genai_response.text)


  with get_db_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute("""
INSERT INTO "message" (course,planitem,content,ai) VALUES (
  %s,%s,%s,%s
)
""",(courseID,planItemID,data.get("message"),False)
      )
      cursor.close()

  with get_db_connection() as connection:
      with connection.cursor() as cursor:
        cursor.execute("""
  INSERT INTO "message" (course,planitem,content,ai) VALUES (
    %s,%s,%s,%s
  )
  """,(courseID,planItemID,obj_genai_response.get("response"),True)
        )
        cursor.close()

  if obj_genai_response.get("note") != None:
    with get_db_connection() as connection:
      with connection.cursor() as cursor:
        cursor.execute("""
INSERT INTO "note" (course,content) VALUES (%s,%s);
""",(courseID,obj_genai_response.get("note")))
        cursor.close()

  return jsonify({"response": obj_genai_response.get("response"),"note": obj_genai_response.get("note")}),200

@app.route("/api/chat/get_conversation/<int:courseID>/<int:planItemID>")
def get_conversation(courseID,planItemID):
  with get_db_connection() as connection:
    with  connection.cursor() as cursor:
      cursor.execute("""
SELECT id, content, ai
FROM "message"
WHERE "message"."planitem" = %s AND "message"."course" = %s;
""",(planItemID,courseID))
      rows = cursor.fetchall()
      cursor.close()
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

  return jsonify(history), 200


@app.route("/")
@app.route("/home")
def index():
  return render_template("index.html")

@app.route("/chat/<int:course_id>/<int:lesson_id>")
def chat(course_id,lesson_id):
  with get_db_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute('SELECT title FROM "course" WHERE id = %s',(course_id,))
      course_name = cursor.fetchone()[0]
      cursor.close()

  with get_db_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute('SELECT content FROM "planItem" WHERE id = %s',(lesson_id,))
      lesson_name = cursor.fetchone()[0]
      cursor.close

  return render_template("chat.html", course_name = course_name, lesson_name=lesson_name, course_id=course_id,lesson_id=lesson_id)


@app.route("/api/chat/get_plan_items/<int:course_id>")
def get_all_plan_items(course_id):
  with get_db_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute('SELECT id,content FROM "planItem" WHERE course = %s',(course_id,))
      rows = cursor.fetchall()
      cursor.close()
  all_plan_items = []
  for row in rows:
    all_plan_items.append({"id": row[0],"content": row[1]})

  return jsonify(all_plan_items),200
