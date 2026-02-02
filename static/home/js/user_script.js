// ========================== PROFILE, SEARCH, NAV ==========================
let profile = document.querySelector('.header .flex .profile-detail');
let searchForm = document.querySelector('.header .flex .search-form');
let navbar = document.querySelector('.navbar');

const userBtn = document.querySelector('#user-btn');
const searchBtn = document.querySelector('#search-btn');
const menuBtn = document.querySelector('#menu-btn');

// Toggle profile detail visibility
if (userBtn) {
    userBtn.addEventListener("click", () => {
        profile.classList.toggle('active');
        searchForm.classList.remove('active');
    });
}

// Toggle search form visibility
if (searchBtn) {
    searchBtn.addEventListener("click", () => {
        searchForm.classList.toggle('active');
        profile.classList.remove('active');
    });
}

// Toggle navbar visibility
if (menuBtn) {
    menuBtn.addEventListener("click", () => {
        navbar.classList.toggle('active');
    });
}

// =============================== SLIDER ===============================
const slides = document.getElementsByClassName('slideBox');
let i = 0;

function nextSlide() {
    if (slides.length > 0) {
        slides[i].classList.remove('active');
        i = (i + 1) % slides.length;
        slides[i].classList.add('active');
    }
}

function prevSlide() {
    if (slides.length > 0) {
        slides[i].classList.remove('active');
        i = (i - 1 + slides.length) % slides.length;
        slides[i].classList.add('active');
    }
}

// ============================ TESTIMONIAL SLIDER ============================
const btn = document.getElementsByClassName('btn1');
const slide = document.getElementById('slide');

if (btn.length > 0 && slide) {
    btn[0].onclick = function () {
        slide.style.transform = 'translateX(0px)';
        updateActive(0);
    };

    btn[1].onclick = function () {
        slide.style.transform = 'translateX(-800px)';
        updateActive(1);
    };

    btn[2].onclick = function () {
        slide.style.transform = 'translateX(-1600px)';
        updateActive(2);
    };

    btn[3].onclick = function () {
        slide.style.transform = 'translateX(-2400px)';
        updateActive(3);
    };

    function updateActive(index) {
        for (let j = 0; j < btn.length; j++) {
            btn[j].classList.remove('active');
        }
        btn[index].classList.add('active');
    }
}

