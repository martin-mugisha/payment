// JavaScript to toggle sidebar visibility on hamburger and close button clicks
document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("sidebar");
  const hamburgerBtn = document.getElementById("hamburger-btn");
  const toggle = document.getElementById("theme-toggle");
  const closeSidebarBtn = document.getElementById("close-sidebar-btn");
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
      closeSidebarBtn.style.display = "none";
    });
  }
  // Earnings Chart
  if (typeof chartLabels !== "undefined" && typeof chartData !== "undefined") {
    const ctx = document.getElementById("earningsChart").getContext("2d");
    new Chart(ctx, {
      type: "line",
      data: {
        labels: chartLabels,
        datasets: [
          {
            label: "Earnings Over Time",
            data: chartData,
            fill: false,
            borderColor: "#007AFF",
            tension: 0.1,
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
});
