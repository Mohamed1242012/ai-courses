# AI Courses

![Google Gemini](https://img.shields.io/badge/google%20gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![MIT](https://img.shields.io/badge/license-MIT-orange)

A web app that helps you learn and develop new skills in a structured way.

## About the project

a Flask web app that generates courses using Google's Gemini API.
It generates a plan and content and you can chat with your AI instants.

## Usage

To host or deploy the website we will use Docker.
First of all, clone the repo.

```bash
git clone https://github.com/Mohamed1242012/ai-courses.git
cd ai-courses
```

Then rename the `example.env` file into `.env`, open the new renamed file.

```bash
# Database - URL must match the data in the docker compose file
POSTGRESQL_URL=postgresql://user:password@postgres:5432/ai-courses
# Gemini API
GENAI_API=AIzaSyBQBf-XhweIAfdjHkhJ78763 # Not a real API Key
```

Change the `GEN_API` variable to your real API key, you can generate one from [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey).

Now start the docker containers

```bash
sudo docker compose up --build -d
```

Open your browser and type `http://localhost:80`

## License

This project is licensed under the GNU General Public License Version 3 - see the [LICENSE](LICENSE) file for details.
