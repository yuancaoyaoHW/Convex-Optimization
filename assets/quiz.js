for (const quiz of document.querySelectorAll("[data-quiz]")) {
  const feedback = quiz.querySelector(".feedback");
  for (const button of quiz.querySelectorAll(".choice")) {
    button.addEventListener("click", () => {
      if (button.dataset.answer === "yes") {
        feedback.textContent = quiz.dataset.correct;
        feedback.style.color = "#166534";
      } else {
        feedback.textContent = quiz.dataset.incorrect;
        feedback.style.color = "#9a3412";
      }
    });
  }
}
