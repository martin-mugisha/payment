document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("sidebar");
  const hamburgerBtn = document.getElementById("hamburger-btn");
  const closeSidebarBtn = document.getElementById("close-sidebar-btn");
  const toggle = document.getElementById("theme-toggle");
  toggle.addEventListener("change", function () {
    document.body.classList.toggle("dark-mode", this.checked);
    document.body.classList.toggle("light-mode", !this.checked);
  });

  if (hamburgerBtn && sidebar) {
    hamburgerBtn.addEventListener("click", () => {
      sidebar.classList.add("active");
      if (closeSidebarBtn) {
        closeSidebarBtn.style.display = "block";
      }
    });
  }

  if (closeSidebarBtn && sidebar) {
  closeSidebarBtn.addEventListener("click", () => {
    sidebar.classList.remove("active");
    console.log('Close Button:', closeSidebarBtn);
    closeSidebarBtn.style.display = "none";
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
});
