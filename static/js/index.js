document.addEventListener("DOMContentLoaded", function (arg) {
  let all_courses_container = document.getElementById("all-courses");

  if (localStorage.getItem("courses") !== null) {
    let all_courses = JSON.parse(localStorage.getItem("courses"));
    for (let course of all_courses) {
      all_courses_container.innerHTML += `
          <div class="col-md-6 col-sm-12 mt-3">
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
          <div class="d-flex justify-content-between">
        <a href="/chat/${course.course_id}/${course.first_lesson}" class="btn btn-dark w-100 me-2">Learn</a>
        <button data-course-id="${course.course_id}" class="btn btn-danger delete-btn"><i class="bi bi-trash-fill"></i></button>
          </div>
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
                  <a href="#create" class="btn btn-dark w-100"
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
    let submitButton = document.getElementById("submit-btn");
    let spinner = document.getElementById("spinner");

    let bigNotes = `My name is ${name.value}.\nI am ${age.value} years old.\n${notes.value}`;

    learn.disabled = true;
    name.disabled = true;
    age.disabled = true;
    notes.disabled = true;
    submitButton.disabled = true;

    spinner.classList.remove("d-none");

    createCourse(learn.value, bigNotes)
      .then((res) => {
        if (!res.ok) {
          throw new Error("Server responded with and error.");
        }
        return res.json();
      })
      .then((json) => {
        const key = "courses";
        let courses = [];
        if (localStorage.getItem(key) !== null) {
          courses = JSON.parse(localStorage.getItem(key));
        }
        courses.push(json);
        localStorage.setItem(key, JSON.stringify(courses, null, 2));

        learn.value = "";
        name.value = "";
        age.value = "";
        notes.value = "";

        spinner.classList.add("d-none");

        const finish_modal = new bootstrap.Modal(
          document.getElementById("finishCourseModal")
        );
        finish_modal.show();
        document
          .getElementById("visitCourseButton")
          .addEventListener("click", function () {
            window.location.href = `/chat/${json.course_id}/${json.first_lesson}`;
          });
      })
      .catch((err) => {
        alert(`Failed to create course. Please try again.\${err}`);
        location.reload();
      });
  });

  document
    .getElementById("all-courses")
    .addEventListener("click", function (e) {
      if (
        e.target.classList.contains("delete-btn") ||
        e.target.closest(".delete-btn")
      ) {
        const button = e.target.closest(".delete-btn");
        const course_id = button.getAttribute("data-course-id");

        // Show confirmation alert
        if (confirm("Are you sure you want to delete this course?")) {
          const key = "courses";
          let courses = JSON.parse(localStorage.getItem(key)) || [];
          courses = courses.filter(
            (course) => course.course_id !== parseInt(course_id)
          );
          if (courses.length === 0) {
            localStorage.removeItem(key); // Remove the key if no courses are left
          } else {
            localStorage.setItem(key, JSON.stringify(courses, null, 2));
          }
          window.location.hash = "#courses";
          window.location.reload();
        }
      }
    });
});
