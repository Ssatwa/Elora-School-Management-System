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
