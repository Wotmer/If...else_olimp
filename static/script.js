let timeoutId;
let lastScroll = 0;
const header = document.querySelector('.header');

const userContainer = document.getElementById('userContainer');
const userMenu = document.getElementById('userMenu');

userContainer.addEventListener('mouseenter', function() {
    clearTimeout(timeoutId);
    userMenu.classList.add('visible');
});

userContainer.addEventListener('mouseleave', function() {
    timeoutId = setTimeout(function() {
        userMenu.classList.remove('visible');
    }, 300);
});

userMenu.addEventListener('mouseenter', function() {
    clearTimeout(timeoutId);
});

userMenu.addEventListener('mouseleave', function() {
    timeoutId = setTimeout(function() {
        userMenu.classList.remove('visible');
    }, 300);
});

window.addEventListener('scroll', () => {
    const currentScroll = window.scrollY;
    header.style.transform = `translateY(${currentScrollY}px)`;
    lastScroll = currentScroll;
});

function showModal(title, description, location, tags, eventType, address, lat, lng, imageUrl) {
    document.getElementById('modal-title').innerText = title;
    document.getElementById('modal-description').innerText = description;
    document.getElementById('modal-location').innerText = location;
    document.getElementById('modal-address').innerText = address;
    document.getElementById('modal-tags').innerText = tags;
    document.getElementById('modal-event-type').innerText = eventType;
    document.getElementById('modal-image').src = imageUrl;

    document.getElementById('modal').style.display = 'block';
}

function hideModal() {
    document.getElementById('modal').style.display = 'none';
    document.getElementById('modal-map').innerHTML = '';
}


window.onclick = function(event) {
    const modal = document.getElementById('modal');
    if (event.target == modal) {
        hideModal();
    }
}

function filterPosts(filterType, value) {
    const url = new URL(window.location);
    url.searchParams.set(filterType, value);
    window.location = url;
}
function switchForm(type) {
  const login = document.getElementById('login-form');
  const register = document.getElementById('register-form');
  if (type === 'login') {
    login.classList.add('active');
    register.classList.remove('active');
  } else {
    login.classList.remove('active');
    register.classList.add('active');
  }
}

function showModal(title, description, location, tags, eventType, lat, lng, imageUrl, organizerName, organizerId, eventDate) {
    const modalImage = document.getElementById('modal-image');
    modalImage.src = imageUrl;

    document.getElementById('modal-title').innerText = title;
    document.getElementById('modal-description').innerText = description;
    document.getElementById('modal-location').innerText = location;
    document.getElementById('modal-date').innerText = new Date(eventDate).toLocaleString();
    document.getElementById('modal-tags').innerText = tags;
    document.getElementById('modal-event-type').innerText = eventType;
    document.getElementById('modal-organizer').innerText = organizerName;

    const organizerLink = document.getElementById('modal-organizer-link');
    organizerLink.href = `/organizer/${organizerId}`;

    document.getElementById('modal').style.display = 'block';
}

function hideModal() {
    document.getElementById('modal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('modal');
    if (event.target == modal) {
        hideModal();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.organizer-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
});