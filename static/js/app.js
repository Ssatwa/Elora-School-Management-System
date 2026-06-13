document.addEventListener("alpine:init", () => {
  Alpine.data("eloraShell", () => ({
    sidebarOpen: false,
    sidebarCollapsed: localStorage.getItem("elora-sidebar") === "collapsed",
    theme: document.documentElement.dataset.theme || "light",
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
      localStorage.setItem(
        "elora-sidebar",
        this.sidebarCollapsed ? "collapsed" : "expanded",
      );
    },
    toggleTheme() {
      this.theme = this.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = this.theme;
      localStorage.setItem("elora-theme", this.theme);
      window.dispatchEvent(new CustomEvent("elora:theme-change"));
    },
  }));
});

document.body.addEventListener("htmx:responseError", () => {
  window.dispatchEvent(new CustomEvent("elora:request-error"));
});
