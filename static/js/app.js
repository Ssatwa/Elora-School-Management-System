const safeStorage = {
  get(key, fallback = null) {
    try {
      return localStorage.getItem(key) ?? fallback;
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch {
      // Storage can be unavailable in privacy-restricted browsing contexts.
    }
  },
};

document.addEventListener("alpine:init", () => {
  Alpine.data("eloraShell", () => ({
    sidebarOpen: false,
    sidebarCollapsed: safeStorage.get("elora-sidebar") === "collapsed",
    theme: document.documentElement.dataset.theme || "light",
    closeMobileSidebar() {
      this.sidebarOpen = false;
    },
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
      safeStorage.set(
        "elora-sidebar",
        this.sidebarCollapsed ? "collapsed" : "expanded",
      );
    },
    toggleTheme() {
      this.theme = this.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = this.theme;
      safeStorage.set("elora-theme", this.theme);
      window.dispatchEvent(new CustomEvent("elora:theme-change"));
    },
  }));
});

document.body.addEventListener("htmx:responseError", () => {
  window.dispatchEvent(new CustomEvent("elora:request-error"));
});

function dashboardChartColors() {
  const styles = getComputedStyle(document.documentElement);
  return {
    text: styles.getPropertyValue("--elora-muted").trim(),
    border: styles.getPropertyValue("--elora-border").trim(),
    primary: styles.getPropertyValue("--elora-primary").trim(),
  };
}

function dashboardChartData(id) {
  const element = document.getElementById(id);
  return element ? JSON.parse(element.textContent) : null;
}

function initializeDashboardCharts() {
  if (typeof Chart === "undefined") return;

  const colors = dashboardChartColors();
  const performanceCanvas = document.getElementById("dashboard-performance-chart");
  const performanceData = dashboardChartData("dashboard-performance-data");
  const attendanceCanvas = document.getElementById("dashboard-attendance-chart");
  const attendanceData = dashboardChartData("dashboard-attendance-data");

  if (performanceCanvas && performanceData) {
    window.eloraPerformanceChart?.destroy();
    window.eloraPerformanceChart = new Chart(performanceCanvas, {
      type: "bar",
      data: {
        labels: performanceData.labels,
        datasets: [{
          data: performanceData.values,
          backgroundColor: colors.primary,
          borderRadius: 8,
          maxBarThickness: 54,
        }],
      },
      options: {
        maintainAspectRatio: false,
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: colors.text } },
          y: {
            beginAtZero: true,
            grid: { color: colors.border },
            ticks: { color: colors.text, precision: 0 },
          },
        },
      },
    });
  }

  if (attendanceCanvas && attendanceData) {
    window.eloraAttendanceChart?.destroy();
    window.eloraAttendanceChart = new Chart(attendanceCanvas, {
      type: "doughnut",
      data: {
        labels: attendanceData.labels,
        datasets: [{
          data: attendanceData.values,
          backgroundColor: ["#2563eb", "#e11d48", "#d97706", "#7c3aed"],
          borderWidth: 0,
          spacing: 3,
        }],
      },
      options: {
        maintainAspectRatio: false,
        responsive: true,
        cutout: "68%",
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: colors.text, boxWidth: 9, usePointStyle: true },
          },
        },
      },
    });
  }
}

document.addEventListener("DOMContentLoaded", initializeDashboardCharts);
window.addEventListener("elora:theme-change", initializeDashboardCharts);

document.addEventListener("submit", (event) => {
  const form = event.target.closest("[data-loading-form]");
  if (!form) return;

  form.querySelectorAll("button[type='submit']").forEach((button) => {
    const loadingLabel = button.dataset.loadingLabel || "Working...";
    button.dataset.originalLabel = button.textContent;
    button.textContent = loadingLabel;
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
  });
});
