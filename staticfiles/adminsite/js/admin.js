document.addEventListener("DOMContentLoaded", () => {

    const toggleBtn = document.querySelector(".mobile-toggle");
    const sidebar = document.querySelector(".sidebar");

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            sidebar.classList.toggle("collapsed");

            // Save state
            localStorage.setItem(
                "sidebarState",
                sidebar.classList.contains("collapsed") ? "collapsed" : "expanded"
            );
        });
    }

    // Restore state on reload
    if (localStorage.getItem("sidebarState") === "collapsed") {
        sidebar.classList.add("collapsed");
    }
    if (window.innerWidth < 992) {
    sidebar.classList.toggle("active");
}

});


