document.addEventListener("DOMContentLoaded", function () {
  console.log("Admin dashboard loaded");

  // Light/Dark toggle - KEEP THIS AS IS
  const toggle = document.getElementById("theme-toggle");
  if (toggle) {
    toggle.addEventListener("change", function () {
      document.body.classList.toggle("dark-mode", this.checked);
      document.body.classList.toggle("light-mode", !this.checked);
    });
  }

  // Earnings Chart - KEEP THIS AS IS
  // Ensure Chart.js library is loaded before this script
  if (
    typeof Chart !== "undefined" &&
    typeof chartLabels !== "undefined" &&
    typeof chartData !== "undefined"
  ) {
    const ctx = document.getElementById("earningsChart")?.getContext("2d"); // Use optional chaining for safety
    if (ctx) {
      new Chart(ctx, {
        type: "bar",
        data: {
          labels: chartLabels,
          datasets: [
            {
              label: "Platform Earnings",
              data: chartData,
              backgroundColor: "#007AFF",
            },
          ],
        },
        options: {
          scales: {
            x: {
              title: {
                display: true,
                text: "Date",
              },
            },
            y: {
              title: {
                display: true,
                text: "Earnings",
              },
            },
          },
        },
      });
    }
  }

  const sidebar = document.querySelector(".sidebar");
  const hamburgerBtn = document.getElementById("hamburger-btn");
  const closeSidebarBtn = document.getElementById("close-sidebar-btn");
  const sidebarOverlay = document.getElementById("sidebar-overlay");

  function openSidebar() {
    if (sidebar) sidebar.classList.add("active");
    if (sidebarOverlay) sidebarOverlay.classList.add("active");
    document.body.classList.add("no-scroll");
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove("active");
    if (sidebarOverlay) sidebarOverlay.classList.remove("active");
    document.body.classList.remove("no-scroll");
  }

  function checkScreenSize() {
    if (!sidebar || !hamburgerBtn) return; // Safety check

    if (window.innerWidth <= 768) {
      // Mobile View
      hamburgerBtn.style.display = "block"; // Show hamburger
      closeSidebar(); // <--- THIS IS KEY: Ensures sidebar is closed on mobile load/resize
      if (closeSidebarBtn) closeSidebarBtn.style.display = "block"; // Show close button
    } else {
      // Desktop View
      hamburgerBtn.style.display = "none"; // Hide hamburger
      sidebar.classList.add("active"); // Sidebar always active on desktop
      document.body.classList.remove("no-scroll");
      if (sidebarOverlay) sidebarOverlay.classList.remove("active");
      if (closeSidebarBtn) closeSidebarBtn.style.display = "none";
    }
  }
  // Event Listeners for sidebar
  if (hamburgerBtn) {
    hamburgerBtn.addEventListener("click", openSidebar);
  }

  if (closeSidebarBtn) {
    closeSidebarBtn.addEventListener("click", closeSidebar);
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", closeSidebar);
  }

  // Close sidebar when a nav link is clicked on mobile
  if (sidebar) {
    sidebar.querySelectorAll("nav a").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.innerWidth <= 768) {
          closeSidebar();
        }
      });
    });
  }

  window.addEventListener("resize", checkScreenSize);
  checkScreenSize(); // <--- THIS IS ALSO KEY: Runs the check immediately on page load
});
