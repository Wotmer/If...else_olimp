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

function hideModal() {
    document.getElementById('modal').style.display = 'none';
    document.getElementById('modal-map').innerHTML = '';
}


window.onclick = function(event) {
    const modal = document.getElementById('modal');
    if (event.target === modal) {
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

function showModal(title, description, location, tags, eventType, lat, lng, imageUrl, organizerName, organizerId, eventDate, eventId, celebrities) {
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

    const celebritiesContainer = document.getElementById('modal-celebrities');
    if (celebritiesContainer) {
        if (celebrities && celebrities.length > 0) {
            let celebritiesHTML = '<h3>Участвуют:</h3><div class="modal-celebrities-list">';
            
            celebrities.forEach(celebrity => {
                celebritiesHTML += `
                    <div class="modal-celebrity-item">
                        ${celebrity.image 
                            ? `<img src="${celebrity.image}" alt="${celebrity.name}" class="modal-celebrity-image">` 
                            : `<div class="modal-celebrity-avatar">${celebrity.name[0].toUpperCase()}</div>`
                        }
                        <div class="modal-celebrity-info">
                            <div class="modal-celebrity-name">${celebrity.name}</div>
                            ${celebrity.role 
                                ? `<div class="modal-celebrity-role">${celebrity.role}</div>` 
                                : ''
                            }
                        </div>
                    </div>
                `;
            });
            
            celebritiesHTML += '</div>';
            celebritiesContainer.innerHTML = celebritiesHTML;
            celebritiesContainer.style.display = 'block';
        } else {
            celebritiesContainer.innerHTML = '';
            celebritiesContainer.style.display = 'none';
        }
    }

    document.getElementById('modal').style.display = 'block';
    
    if (eventId) {
        loadEventReviews(eventId);

        const reviewForm = document.getElementById('event-review-form');
        if (reviewForm) {
            reviewForm.setAttribute('data-event-id', eventId);
            reviewForm.action = `/event/${eventId}/review`;
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e) {
        const link = e.target.closest('.organizer-link');
        if (link) {
            e.stopPropagation();
        }
    });
    document.querySelectorAll('.post-content a[href*="organizer_profile"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
});
function loadEventReviews(eventId) {
    fetch(`/event/${eventId}/reviews`)
        .then(response => response.json())
        .then(data => {
            const reviewsContainer = document.getElementById('event-reviews');
            reviewsContainer.innerHTML = '';
            
            if (data.reviews.length === 0) {
                reviewsContainer.innerHTML = '<p>Пока нет отзывов</p>';
                return;
            }
            
            data.reviews.forEach(review => {
                const reviewElem = document.createElement('div');
                reviewElem.className = 'review-item';
                
                const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
                
                reviewElem.innerHTML = `
                    <div class="review-header">
                        <span class="reviewer-name">${review.username}</span>
                        <div class="rating">${stars}</div>
                        <span class="review-date">${review.date}</span>
                    </div>
                    <div class="review-content">${review.comment}</div>
                `;
                
                reviewsContainer.appendChild(reviewElem);
            });
            
            const reviewForm = document.getElementById('event-review-form');
            if (reviewForm) {
                reviewForm.setAttribute('data-event-id', eventId);
                reviewForm.action = `/event/${eventId}/review`;
                
                const userReview = data.reviews.find(r => r.is_current_user);
                if (userReview) {
                    document.querySelector(`input[name="rating"][value="${userReview.rating}"]`).checked = true;
                    document.querySelector('textarea[name="comment"]').value = userReview.comment;
                }
            }
        })
        .catch(error => console.error('Ошибка загрузки отзывов:', error));
}

document.addEventListener('DOMContentLoaded', function() {
    const eventReviewForm = document.getElementById('event-review-form');
    if (eventReviewForm) {
        eventReviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const eventId = this.getAttribute('data-event-id');
            const formData = new FormData(this);
            
            fetch(`/event/${eventId}/review`, {
                method: 'POST',
                body: formData
            }).then(response => {
                if (response.ok) {
                    alert('Отзыв успешно отправлен!');
                    loadEventReviews(eventId);
                }
            }).catch(error => {
                console.error('Ошибка:', error);
            });
        });
    }
});

const originalShowModal = window.showModal;
window.showModal = function(title, description, location, tags, eventType, lat, lng, imageUrl, organizerName, organizerId, eventDate, eventId) {
    if (originalShowModal) {
        originalShowModal(title, description, location, tags, eventType, lat, lng, imageUrl, organizerName, organizerId, eventDate);
    } else {
        document.getElementById('modal-title').innerText = title;
        document.getElementById('modal-description').innerText = description;
        document.getElementById('modal-location').innerText = location;
        document.getElementById('modal-date').innerText = new Date(eventDate).toLocaleString();
        document.getElementById('modal-tags').innerText = tags;
        document.getElementById('modal-event-type').innerText = eventType;
        document.getElementById('modal-organizer').innerText = organizerName;
        
        const modalImage = document.getElementById('modal-image');
        if (modalImage) modalImage.src = imageUrl;
        
        const organizerLink = document.getElementById('modal-organizer-link');
        if (organizerLink) organizerLink.href = `/organizer/${organizerId}`;
        
        document.getElementById('modal').style.display = 'block';
    }
    
    if (eventId) {
        loadEventReviews(eventId);
        
        const reviewForm = document.getElementById('event-review-form');
        if (reviewForm) {
            reviewForm.setAttribute('data-event-id', eventId);
            reviewForm.action = `/event/${eventId}/review`;
        }
    }
};

document.addEventListener('DOMContentLoaded', function() {
    const interestSliders = document.querySelectorAll('.interest-slider input[type="range"]');
    if (interestSliders) {
        interestSliders.forEach(slider => {
            const valueDisplay = slider.nextElementSibling;
            
            if (valueDisplay) {
                valueDisplay.textContent = slider.value;
            }
            
            slider.addEventListener('input', function() {
                if (valueDisplay) {
                    valueDisplay.textContent = this.value;
                }
            });
        });
    }
});