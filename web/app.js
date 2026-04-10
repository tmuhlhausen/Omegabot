const actions = document.querySelectorAll(".action");
actions.forEach((btn) => {
  btn.addEventListener("click", () => {
    actions.forEach((x) => x.classList.remove("active"));
    btn.classList.add("active");
  });
});

const themeToggle = document.getElementById("themeToggle");
themeToggle?.addEventListener("click", () => {
  document.body.classList.toggle("light");
});
