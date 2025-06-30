// JavaScript to toggle navigation panel visibility on hamburger and close button clicks for index.html
document.addEventListener("DOMContentLoaded", () => {
  const navLinks = document.getElementById("nav-links");
  const hamburgerBtn = document.getElementById("hamburger-btn");
  const closeNavBtn = document.getElementById("close-nav-btn");

  if (hamburgerBtn && navLinks) {
    hamburgerBtn.addEventListener("click", () => {
      navLinks.classList.add("active");
      if (closeNavBtn) {
        closeNavBtn.style.display = "block";
      }
    });
  }

  if (closeNavBtn && navLinks) {
    closeNavBtn.addEventListener("click", () => {
      navLinks.classList.remove("active");
      closeNavBtn.style.display = "none";
    });
  }
});
