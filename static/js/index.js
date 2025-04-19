document.addEventListener("DOMContentLoaded", function (arg) {
  let all_courses_container = document.getElementById("all-courses");

  if (localStorage.getItem("courses") !== null) {
    let all_courses = JSON.parse(localStorage.getItem("courses"));
    for (let course of all_courses) {
      all_courses_container.innerHTML += `
          <div class="col-6">
            <div class="card">
                <div class="card-body">
                  <div class="d-flex justify-content-center mb-3">
                    <div class="icon-wrapper text-center">
                      <i class="bi bi-book-fill display-1"></i>
                    </div>
                  </div>
                  <h5 class="card-title">${course.title}</h5>
                  <p class="card-text">
                    ${course.description}
                  </p>
                </div>
                <div class="card-footer">
                  <a href="/chat/${course.course_id}/${course.first_lesson}" class="btn btn-light w-100">Learn</a>
                </div>
              </div>
              </div>
    `;
    }
  } else {
    all_courses_container.innerHTML += `
                <div class="col-6">
              <div class="card">
                <div class="card-body">
                  <div class="d-flex justify-content-center mb-3">
                    <div class="icon-wrapper text-center">
                      <i class="bi bi-ban display-1"></i>
                    </div>
                  </div>
                  <h5 class="card-title">Oh no</h5>
                  <p class="card-text">You dont have any courses yet.</p>
                </div>
                <div class="card-footer">
                  <a href="#create" class="btn btn-light w-100"
                    >Create Course</a
                  >
                </div>
              </div>
            </div>
    `;
  }

  async function createCourse(title, notes) {
    const response = await fetch("/api/course", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ learn: title, notes: notes }),
    });
    return response;
  }

  createForm = document.getElementById("new_course_form");
  createForm.addEventListener("submit", function (e) {
    e.preventDefault();
    let learn = document.getElementById("learn");
    let name = document.getElementById("name");
    let age = document.getElementById("age");
    let notes = document.getElementById("notes");

    let bigNotes = `My name is ${name.value}.\nI am ${age.value} years old.\n${notes.value}`;

    createCourse(learn.value, bigNotes)
      .then((res) => res.json())
      .then((json) => {
        const key = "courses";
        let courses = [];
        if (localStorage.getItem(key) !== null) {
          courses = JSON.parse(localStorage.getItem(key));
        }
        courses.push(json);
        localStorage.setItem(key, JSON.stringify(courses, null, 2));
        window.location.hash = "#courses";
        location.reload();
      });
  });
});
