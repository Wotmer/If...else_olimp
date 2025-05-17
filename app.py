from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
from sqlalchemy.orm import joinedload
from jinja2 import Environment
import os
from werkzeug.utils import secure_filename
import folium
from sqlalchemy import or_, and_, case, func, desc
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select

app = Flask(__name__)
app.secret_key = 'x7k9p2m4n6b8v0c1z3q5w8e9r2t4y6u'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
Session(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
env = Environment()
env.filters['datetime_format'] = lambda dt: dt.strftime('%d.%m.%Y %H:%M') if dt else ''
app.jinja_env.filters['datetime_format'] = env.filters['datetime_format']


from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='participant')
    is_admin = db.Column(db.Boolean, default=False)

    @hybrid_property
    def avg_rating(self):
        reviews = OrganizerReview.query.filter_by(organizer_id=self.id).all()
        if not reviews:
            return 0
        return sum(review.rating for review in reviews) / len(reviews)
    
    @avg_rating.expression
    def avg_rating(cls):
        return (select([func.avg(OrganizerReview.rating)])
                .where(OrganizerReview.organizer_id == cls.id)
                .label('avg_rating'))


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    format = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(200))
    date_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    event_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    organizer = db.relationship('User', backref='events')
    tags = db.relationship('Tag', secondary='event_tag', backref='events')
    reviews = db.relationship('EventReview', back_populates='event', lazy=True)

    def notify_subscribers(self):
        subscribers = [sub.user for sub in self.organizer.subscribers]
        for subscriber in subscribers:
            print(f"Уведомление для {subscriber.username}: новое мероприятие '{self.title}'")

    @hybrid_property
    def avg_rating(self):
        reviews_list = db.session.query(EventReview).filter(EventReview.event_id == self.id).all()
        if not reviews_list:
            return 0
        return sum(review.rating for review in reviews_list) / len(reviews_list)
    
    @avg_rating.expression
    def avg_rating(cls):
        return (select([func.avg(EventReview.rating)])
                .where(EventReview.event_id == cls.id)
                .label('avg_rating'))


class EventTag(db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref='subscriptions')
    organizer = db.relationship('User', foreign_keys=[organizer_id], backref='subscribers')

class EventReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # от 1 до 5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    event = db.relationship('Event', back_populates='reviews')
    user = db.relationship('User', backref=db.backref('event_reviews', lazy='dynamic'))

class OrganizerReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organizer = db.relationship('User', foreign_keys=[organizer_id], 
                                backref=db.backref('received_reviews', lazy='dynamic'))
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], 
                              backref=db.backref('given_reviews', lazy='dynamic'))

class UserInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)
    interest_level = db.Column(db.Integer, default=0)  # чем выше, тем больше интерес
    
    user = db.relationship('User', backref=db.backref('interests', lazy='dynamic'))
    tag = db.relationship('Tag', backref=db.backref('interested_users', lazy='dynamic'))

class Celebrity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    events = db.relationship('Event', secondary='event_celebrity', backref='celebrities')

class EventCelebrity(db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    celebrity_id = db.Column(db.Integer, db.ForeignKey('celebrity.id'), primary_key=True)
    role = db.Column(db.String(50))


with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        hashed_pwd = bcrypt.generate_password_hash('admin').decode('utf-8')
        admin = User(username='admin', email='admin@example.com', password=hashed_pwd, role='organizer', is_admin=True)
        db.session.add(admin)
    if not User.query.filter_by(username='participant1').first():
        hashed_pwd = bcrypt.generate_password_hash('pass123').decode('utf-8')
        user1 = User(username='participant1', email='participant1@example.com', password=hashed_pwd, role='participant')
        db.session.add(user1)
    if not User.query.filter_by(username='organizer1').first():
        hashed_pwd = bcrypt.generate_password_hash('org456').decode('utf-8')
        user2 = User(username='organizer1', email='organizer1@example.com', password=hashed_pwd, role='organizer')
        db.session.add(user2)

    if not Tag.query.first():
        tags = ['музыка', 'отдых', 'искусство', 'культура', 'концерт']
        for tag_name in tags:
            db.session.add(Tag(name=tag_name))

    if not Event.query.first():
        organizer = User.query.filter_by(username='organizer1').first()
        events = [
            {
                "title": "Концерт в Минске",
                "description": "Живой концерт популярной группы.",
                "format": "offline",
                "location": "ул. Ленина, 10, Минск",
                "date_time": datetime(2024, 11, 15, 19, 0),
                "duration": 120,
                "lat": 53.9007393,
                "lng": 27.5558223,
                "event_type": "Концерт",
                "tags": ["музыка", "концерт"],
                "image": "../static/images/event1.png"
            },
            {
                "title": "Выставка картин",
                "description": "Экспозиция современных художников.",
                "format": "offline",
                "location": "ул. Советская, 5, Гродно",
                "date_time": datetime(2024, 11, 20, 10, 0),
                "duration": 180,
                "lat": 53.6788563,
                "lng": 23.827121,
                "event_type": "Выставка",
                "tags": ["искусство", "культура"],
                "image": "../static/images/event2.png"
            }
        ]
        for event_data in events:
            event = Event(
                title=event_data['title'],
                description=event_data['description'],
                organizer_id=organizer.id,
                format=event_data['format'],
                location=event_data['location'],
                date_time=event_data['date_time'],
                duration=event_data['duration'],
                lat=event_data['lat'],
                lng=event_data['lng'],
                event_type=event_data['event_type']
            )
            db.session.add(event)
            db.session.flush()
            for tag_name in event_data['tags']:
                tag = Tag.query.filter_by(name=tag_name).first()
                if tag:
                    db.session.add(EventTag(event_id=event.id, tag_id=tag.id))
    db.session.commit()

    concert = Event.query.filter_by(title='Концерт в Минске').first()
    if concert:
        concert.lat = 53.90297238393145
        concert.lng = 27.555303865441697
        db.session.commit()

    exhibition = Event.query.filter_by(title='Выставка картин').first()
    if exhibition:
        exhibition.lat = 53.67958056885761
        exhibition.lng = 23.83001131069645
        db.session.commit()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def home():
    search_query = request.args.get('search', '')
    selected_tag = request.args.get('tag', '')
    
    query = db.session.query(Event).filter(Event.is_active == True)
    
    if search_query:
        query = query.filter(
            or_(
                Event.title.ilike(f'%{search_query}%'),
                Event.description.ilike(f'%{search_query}%'),
                Event.location.ilike(f'%{search_query}%')
            )
        )
    
    if selected_tag:
        tag = Tag.query.filter_by(name=selected_tag).first()
        if tag:
            query = query.join(EventTag).filter(EventTag.tag_id == tag.id)
    
    posts = query.order_by(Event.date_time.asc()).all()
    
    tags = Tag.query.all()
    
    recommended_events = []
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if user:
            recommended_events = Event.query.filter(
                Event.is_active == True,
                Event.date_time >= datetime.utcnow()
            ).order_by(Event.date_time.asc()).limit(5).all()
    
    events_with_celebrities = {}
    for event in posts + recommended_events:
        if event.celebrities:
            events_with_celebrities[event.id] = {
                'celebrities': [
                    {
                        'name': celeb.name,
                        'image': celeb.image_url,
                        'role': next((ec.role for ec in EventCelebrity.query.filter_by(
                            event_id=event.id, celebrity_id=celeb.id).all()), '')
                    } for celeb in event.celebrities
                ]
            }
    
    # Возвращаем шаблон с данными
    return render_template('index.html', 
                           posts=posts, 
                           tags=tags, 
                           selected_tag=selected_tag,
                           search_query=search_query,
                           recommended_events=recommended_events,
                           events_with_celebrities=events_with_celebrities)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['username'] = username
            session['role'] = user.role
            session['is_admin'] = user.is_admin
            return redirect(url_for('home'))
        return render_template('login.html', error="Неверный логин или пароль")
    return render_template('login.html', error=None)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if role not in ['participant', 'organizer']:
            role = 'participant'

        if not username or not email or not password:
            return render_template('register.html', error="Все поля обязательны для заполнения")

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Пользователь с таким именем уже существует")

        if User.query.filter_by(email=email).first():
            return render_template('register.html', error="Этот email уже зарегистрирован")

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()

        session['username'] = username
        session['role'] = role
        return redirect(url_for('home'))

    return render_template('register.html', error=None)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('home'))


@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if 'username' not in session or session['role'] != 'organizer':
        return redirect(url_for('home'))

    tags = Tag.query.all()
    celebrities = Celebrity.query.all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        format_type = request.form.get('format')
        location = request.form.get('location')
        date_time = datetime.strptime(request.form.get('date_time'), '%Y-%m-%dT%H:%M')
        duration = int(request.form.get('duration'))
        lat = float(request.form.get('lat', 0))
        lng = float(request.form.get('lng', 0))
        event_type = request.form.get('event_type')
        selected_tags = request.form.getlist('tags')
        selected_celebrities = request.form.getlist('celebrities')
        celebrity_roles = request.form.getlist('celebrity_roles')
        image_url = None

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(upload_path)
                image_url = url_for('static', filename=f'uploads/{filename}')

        user = User.query.filter_by(username=session['username']).first()
        event = Event(
            title=title,
            description=description,
            organizer_id=user.id,
            format=format_type,
            location=location,
            date_time=date_time,
            duration=duration,
            lat=lat,
            lng=lng,
            event_type=event_type,
            image_url=image_url
        )
        db.session.add(event)
        db.session.flush()
        for tag_id in selected_tags:
            tag = Tag.query.get(tag_id)
            if tag:
                db.session.add(EventTag(event_id=event.id, tag_id=tag.id))

        for i, celebrity_id in enumerate(selected_celebrities):
            role = ""
            if i < len(celebrity_roles):
                role = celebrity_roles[i]
                
            celebrity = Celebrity.query.get(celebrity_id)
            if celebrity:
                db.session.add(EventCelebrity(
                    event_id=event.id, 
                    celebrity_id=celebrity.id,
                    role=role
                ))
                
        db.session.commit()

        event.notify_subscribers()

        flash('Мероприятие успешно добавлено', 'success')
        return redirect(url_for('home'))

    return render_template('add_event.html', tags=tags, celebrities=celebrities)


@app.route('/subscribe/<int:organizer_id>', methods=['POST'])
def subscribe(organizer_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return redirect(url_for('login'))

    if user.id == organizer_id:
        flash('Нельзя подписаться на самого себя', 'error')
        return redirect(request.referrer or url_for('home'))

    existing = Subscription.query.filter_by(
        user_id=user.id,
        organizer_id=organizer_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash('Вы отписались от организатора', 'success')
    else:
        subscription = Subscription(
            user_id=user.id,
            organizer_id=organizer_id
        )
        db.session.add(subscription)
        db.session.commit()
        flash('Вы подписались на организатора', 'success')

    return redirect(request.referrer or url_for('home'))


@app.route('/map', methods=['GET'])
def show_map():
    search_query = request.args.get('search', '')
    selected_tag = request.args.get('tag', '')

    query = Event.query.filter_by(is_active=True)

    if search_query:
        query = query.filter(
            or_(
                Event.title.ilike(f'%{search_query}%'),
                Event.description.ilike(f'%{search_query}%'),
                Event.location.ilike(f'%{search_query}%')
            )
        )
    
    if selected_tag:
        tag = Tag.query.filter_by(name=selected_tag).first()
        if tag:
            query = query.join(EventTag).filter(EventTag.tag_id == tag.id)
    
    events = query.all()

    tags = Tag.query.all()

    events_with_celebrities = {}
    for event in events:
        if event.celebrities:
            events_with_celebrities[event.id] = True
    
    return render_template('map.html', 
                          events=events, 
                          tags=tags,
                          selected_tag=selected_tag,
                          search_query=search_query,
                          events_with_celebrities=events_with_celebrities)


@app.route('/generate_map')
def generate_map():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    if not lat or not lng:
        return "<div>No coordinates provided</div>"

    map_html = f"""
    <div id="map" style="width: 100%; height: 100%;"></div>
    <script src="https://api-maps.yandex.ru/2.1/?apikey=YOUR_API_KEY&lang=ru_RU"></script>
    <script>
        ymaps.ready(init);
        function init() {{
            var myMap = new ymaps.Map("map", {{
                center: [{lat}, {lng}],
                zoom: 15
            }});

            var myPlacemark = new ymaps.Placemark([{lat}, {lng}], {{
                hintContent: 'Место мероприятия'
            }});

            myMap.geoObjects.add(myPlacemark);
        }}
    </script>
    """
    return map_html


@app.route('/add_tag', methods=['GET', 'POST'])
def add_tag():
    if 'username' not in session or session['role'] != 'organizer':
        return redirect(url_for('home'))
    if request.method == 'POST':
        tag_name = request.form.get('tag_name')
        if tag_name and not Tag.query.filter_by(name=tag_name).first():
            db.session.add(Tag(name=tag_name))
            db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_tag.html')


@app.route('/organizer/<int:organizer_id>')
def organizer_profile(organizer_id):
    try:
        organizer = db.session.query(User).options(
            joinedload(User.subscribers)
        ).get(organizer_id)

        if not organizer:
            flash('Пользователь не найден', 'error')
            return redirect(url_for('home'))

        if organizer.role != 'organizer':
            flash('Этот пользователь не является организатором', 'info')
            return redirect(url_for('home'))

        events = db.session.query(Event).filter(
            Event.organizer_id == organizer_id,
            Event.is_active == True
        ).order_by(Event.date_time.desc()).all()

        is_subscribed = False
        if 'username' in session:
            current_user = User.query.filter_by(username=session['username']).first()
            if current_user:
                is_subscribed = db.session.query(Subscription).filter(
                    Subscription.user_id == current_user.id,
                    Subscription.organizer_id == organizer_id
                ).first() is not None
                
        organizer_reviews = OrganizerReview.query.filter_by(
            organizer_id=organizer_id
        ).order_by(OrganizerReview.created_at.desc()).all()
        
        # calculated_avg_rating = 0
        # if organizer_reviews:
        #     calculated_avg_rating = sum(review.rating for review in organizer_reviews) / len(organizer_reviews)

        return render_template(
            'organizer_profile.html',
            organizer=organizer,
            events=events,
            subscribers_count=len(organizer.subscribers),
            is_subscribed=is_subscribed,
            organizer_reviews=organizer_reviews
            # avg_rating=calculated_avg_rating
        )

    except Exception as e:
        app.logger.error(f"Error in organizer_profile: {str(e)}")
        flash('Произошла ошибка при загрузке страницы', 'error')
        return redirect(url_for('home'))

@app.route('/event/<int:event_id>/review', methods=['POST'])
def add_event_review(event_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    rating = int(request.form.get('rating', 0))
    comment = request.form.get('comment', '')
    
    if not (1 <= rating <= 5):
        flash('Рейтинг должен быть от 1 до 5', 'error')
        return redirect(url_for('home'))
    
    user = User.query.filter_by(username=session['username']).first()
    event = Event.query.get(event_id)
    
    if not event:
        flash('Мероприятие не найдено', 'error')
        return redirect(url_for('home'))
    
    existing_review = EventReview.query.filter_by(
        event_id=event_id, user_id=user.id
    ).first()
    
    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
        db.session.commit()
        flash('Ваш отзыв обновлен!', 'success')
    else:
        review = EventReview(
            event_id=event_id,
            user_id=user.id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        db.session.commit()
        flash('Спасибо за ваш отзыв!', 'success')
    
    for tag in event.tags:
        interest = UserInterest.query.filter_by(
            user_id=user.id, tag_id=tag.id
        ).first()
        
        if interest:
            interest.interest_level += rating 
        else:
            interest = UserInterest(
                user_id=user.id,
                tag_id=tag.id,
                interest_level=rating
            )
            db.session.add(interest)
    
    db.session.commit()
    return redirect(request.referrer or url_for('home'))

@app.route('/organizer/<int:organizer_id>/review', methods=['POST'])
def add_organizer_review(organizer_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    rating = int(request.form.get('rating', 0))
    comment = request.form.get('comment', '')
    
    if not (1 <= rating <= 5):
        flash('Рейтинг должен быть от 1 до 5', 'error')
        return redirect(url_for('home'))
    
    reviewer = User.query.filter_by(username=session['username']).first()
    
    if reviewer.id == organizer_id:
        flash('Вы не можете оставить отзыв самому себе', 'error')
        return redirect(url_for('home'))
    
    organizer = User.query.get(organizer_id)
    if not organizer or organizer.role != 'organizer':
        flash('Организатор не найден', 'error')
        return redirect(url_for('home'))
    
    existing_review = OrganizerReview.query.filter_by(
        organizer_id=organizer_id, reviewer_id=reviewer.id
    ).first()
    
    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
        db.session.commit()
        flash('Ваш отзыв обновлен!', 'success')
    else:
        review = OrganizerReview(
            organizer_id=organizer_id,
            reviewer_id=reviewer.id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        db.session.commit()
        flash('Спасибо за ваш отзыв!', 'success')

    return redirect(request.referrer or url_for('home'))

@app.route('/event/<int:event_id>/reviews')
def get_event_reviews(event_id):
    reviews = EventReview.query.filter_by(event_id=event_id).order_by(EventReview.created_at.desc()).all()

    current_user_id = None
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        if user:
            current_user_id = user.id

    reviews_data = []
    for review in reviews:
        reviews_data.append({
            'id': review.id,
            'username': review.user.username,
            'rating': review.rating,
            'comment': review.comment,
            'date': review.created_at.strftime('%d.%m.%Y'),
            'is_current_user': review.user_id == current_user_id
        })

    return jsonify({'reviews': reviews_data})

@app.route('/user_preferences', methods=['GET', 'POST'])
def user_preferences():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    tags = Tag.query.all()
    
    user_interests = UserInterest.query.filter_by(user_id=user_id).all()
    user_interests_dict = {interest.tag_id: interest.interest_level for interest in user_interests}
    
    if request.method == 'POST':
        UserInterest.query.filter_by(user_id=user_id).delete()
        
        for tag in tags:
            interest_level = request.form.get(f'interest_{tag.id}')
            if interest_level and interest_level != '0':
                new_interest = UserInterest(
                    user_id=user_id,
                    tag_id=tag.id,
                    interest_level=int(interest_level)
                )
                db.session.add(new_interest)
        
        db.session.commit()
        flash('Ваши интересы успешно обновлены!', 'success')
        return redirect(url_for('home'))
    
    return render_template('preferences.html', tags=tags, user_interests=user_interests_dict)

@app.route('/add_celebrity', methods=['GET', 'POST'])
def add_celebrity():
    if 'username' not in session or session['role'] != 'organizer':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        image_url = None

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(upload_path)
                image_url = url_for('static', filename=f'uploads/{filename}')

        celebrity = Celebrity(
            name=name,
            description=description,
            image_url=image_url,
            is_verified=False
        )

        db.session.add(celebrity)
        db.session.commit()
        flash('Известная личность успешно добавлена', 'success')
        return redirect(url_for('home'))

    return render_template('add_celebrity.html')


@app.route('/event/<int:event_id>/add_celebrity', methods=['POST'])
def add_celebrity_to_event(event_id):
    if 'username' not in session or session['role'] != 'organizer':
        return redirect(url_for('login'))

    celebrity_id = request.form.get('celebrity_id')
    role = request.form.get('role')

    event = Event.query.get(event_id)
    user = User.query.filter_by(username=session['username']).first()

    if not event or event.organizer_id != user.id:
        flash('Мероприятие не найдено или у вас нет прав для его редактирования', 'error')
        return redirect(url_for('home'))

    celebrity = Celebrity.query.get(celebrity_id)
    if not celebrity:
        flash('Указанная известная личность не найдена', 'error')
        return redirect(url_for('home'))

    existing = EventCelebrity.query.filter_by(event_id=event_id, celebrity_id=celebrity_id).first()
    if existing:
        flash('Эта известная личность уже добавлена к данному мероприятию', 'info')
        return redirect(url_for('home'))

    event_celebrity = EventCelebrity(
        event_id=event_id,
        celebrity_id=celebrity_id,
        role=role
    )

    db.session.add(event_celebrity)
    db.session.commit()
    flash('Известная личность успешно добавлена к мероприятию', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)