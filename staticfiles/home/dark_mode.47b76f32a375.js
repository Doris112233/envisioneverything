// Check for saved user preference and apply on page load
document.addEventListener("DOMContentLoaded", function () {
  // Check if dark mode is saved in localStorage
  if (localStorage.getItem("darkMode") === "enabled") {
    document.body.classList.add("dark-mode");
    document.getElementById("checkbox").checked = true;
  }
});

function toggleDarkMode() {
  // Toggle dark mode class on body
  document.body.classList.toggle("dark-mode");

  // Save preference to localStorage and update the icon
  if (document.body.classList.contains("dark-mode")) {
    localStorage.setItem("darkMode", "enabled");
  } else {
    localStorage.setItem("darkMode", "disabled");
  }
}