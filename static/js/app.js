document.body.addEventListener("htmx:responseError", () => {
  window.dispatchEvent(new CustomEvent("elora:request-error"));
});
