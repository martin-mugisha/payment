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
  // Excel Upload and Download functionality
  // Note: Include the following CDN in your HTML template:
  // <script src="https://cdn.sheetjs.com/xlsx-latest/package/dist/xlsx.full.min.js"></script>

  // Upload Excel file and parse data
  const excelUploadInput = document.getElementById("excelUploadInput");
  if (excelUploadInput) {
    excelUploadInput.addEventListener("change", (event) => {
      const file = event.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: "array" });
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
        console.log("Excel Data:", jsonData);
        // TODO: Process jsonData as needed
      };
      reader.readAsArrayBuffer(file);
    });
  }

  // Download data as Excel file
  const downloadExcelBtn = document.getElementById("downloadExcelBtn");
  if (downloadExcelBtn) {
    downloadExcelBtn.addEventListener("click", () => {
      // Example data to export
      const data = [
        ["Name", "Age", "Email"],
        ["John Doe", 30, "john@example.com"],
        ["Jane Smith", 25, "jane@example.com"],
      ];
      const worksheet = XLSX.utils.aoa_to_sheet(data);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Sheet1");
      XLSX.writeFile(workbook, "export.xlsx");
    });
  }

  // Search records in table by name and number
  const nameSearchInput = document.getElementById("nameSearchInput");
  const numberSearchInput = document.getElementById("numberSearchInput");
  const recordsTable = document.getElementById("recordsTable");

  function filterTable() {
    const nameFilter = nameSearchInput
      ? nameSearchInput.value.toLowerCase()
      : "";
    const numberFilter = numberSearchInput
      ? numberSearchInput.value.toLowerCase()
      : "";

    if (!recordsTable) return;

    const rows = recordsTable.getElementsByTagName("tr");
    for (let i = 1; i < rows.length; i++) {
      const cells = rows[i].getElementsByTagName("td");
      const nameCell = cells[0] ? cells[0].textContent.toLowerCase() : "";
      const numberCell = cells[1] ? cells[1].textContent.toLowerCase() : "";

      if (nameCell.includes(nameFilter) && numberCell.includes(numberFilter)) {
        rows[i].style.display = "";
      } else {
        rows[i].style.display = "none";
      }
    }
  }

  if (nameSearchInput) {
    nameSearchInput.addEventListener("input", filterTable);
  }
  if (numberSearchInput) {
    numberSearchInput.addEventListener("input", filterTable);
  }

  // Render Weekly Chart
  const weeklyChartCanvas = document.getElementById("weeklyChart");
  if (
    weeklyChartCanvas &&
    typeof weeklyLabels !== "undefined" &&
    typeof weeklyData !== "undefined"
  ) {
    new Chart(weeklyChartCanvas.getContext("2d"), {
      type: "line",
      data: {
        labels: weeklyLabels,
        datasets: [
          {
            label: "Weekly Data",
            data: weeklyData,
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
              text: "Day",
            },
          },
          y: {
            title: {
              display: true,
              text: "Value",
            },
          },
        },
      },
    });
  }

  // Render Monthly Chart
  const monthlyChartCanvas = document.getElementById("monthlyChart");
  if (
    monthlyChartCanvas &&
    typeof monthlyLabels !== "undefined" &&
    typeof monthlyData !== "undefined"
  ) {
    new Chart(monthlyChartCanvas.getContext("2d"), {
      type: "bar",
      data: {
        labels: monthlyLabels,
        datasets: [
          {
            label: "Monthly Data",
            data: monthlyData,
            backgroundColor: "#4caf50",
          },
        ],
      },
      options: {
        scales: {
          x: {
            title: {
              display: true,
              text: "Week",
            },
          },
          y: {
            title: {
              display: true,
              text: "Value",
            },
          },
        },
      },
    });
  }
});
