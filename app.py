from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import requests
from models import db, User, City
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
from models import db, User 
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from datetime import datetime







app = Flask(__name__)
load_dotenv()


app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')



mail = Mail(app)


db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@app.route("/update_settings", methods=["POST"])
@login_required
def update_settings():
    wants_email = True if request.form.get("wants_email") == "yes" else False
    email_hour = int(request.form.get("email_hour") or 9)

    current_user.wants_email = wants_email
    current_user.email_hour = email_hour
    db.session.commit()

    return redirect(url_for("dashboard"))



def send_daily_weather_email():
    with app.app_context():
        now_hour = datetime.now().hour  # şimdiki saat
        users = User.query.filter_by(wants_email=True).all()

        for user in users:
            if user.email_hour != now_hour:
                continue  # saat uyuşmuyorsa atla

            city_list = user.cities
            if not city_list:
                continue

            body_html = "<h3>Bugün için hava durumu raporunuz:</h3><ul>"

            for city in city_list:
                weather = get_weather_data(city.name)
                if weather:
                    body_html += f"""
                    <li>
                        <strong>{weather['city']}</strong> |
                        {weather['temperature']}°C |
                        {weather['description']} <br>
                        <img src="http://openweathermap.org/img/wn/{weather['icon']}@2x.png" alt="icon">
                    </li>
                    """
            body_html += "</ul>"

            msg = Message(
                subject="Günlük Hava Durumu Raporunuz",
                sender=app.config['MAIL_USERNAME'],
                recipients=[user.email],
                html=body_html
            )
            mail.send(msg)

        
    

scheduler = BackgroundScheduler()
scheduler.add_job(func=send_daily_weather_email, trigger="cron", minute=0)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())


def get_local_background(temp):
    if temp <= 5:
        return url_for("static", filename="images/backgrounds/cold.jpg")
    elif temp <= 12:
        return url_for("static", filename="images/backgrounds/cool.jpg")
    elif temp <= 22:
        return url_for("static", filename="images/backgrounds/mild.jpg")    
    elif temp <= 28:
        return url_for("static", filename="images/backgrounds/warm.jpg")
    else:
        return url_for("static", filename="images/backgrounds/hot.jpg")




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("index.html")

def is_valid_city(city_name):
    api_key = os.getenv("OPENWEATHER_ACCESS_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&lang=en"
    response = requests.get(url)
    return response.status_code == 200 # 200 means valid city -> true, 404 means not valid city

@app.route("/login", methods=["GET", "POST"])
def login():
    message = None
    message_type = None

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            message = "Wrong email or password"
            message_type = "error"

    return render_template("login.html", message=message, message_type=message_type)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if User.query.filter_by(email=email).first():
            flash("Bu e-posta zaten kayıtlı.")
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Kayıt başarılı. Giriş yapabilirsiniz.")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    message = ""
    message_type = ""  # success / error

    if request.method == "POST":
        city_name = request.form.get("city")

        if not city_name:
            message = "Please enter a city name"
            message_type = "error"

        elif not is_valid_city(city_name):
            message = "City does not exist"
            message_type = "error"

        else:
            existing_city = City.query.filter_by(name=city_name, user_id=current_user.id).first()
            if existing_city:
                message = f"{city_name} is already listed"
                message_type = "error"
            else:
                new_city = City(name=city_name, user_id=current_user.id)
                db.session.add(new_city)
                db.session.commit()
                message = f"{city_name} added successfully"
                message_type = "success"

    cities = City.query.filter_by(user_id=current_user.id).all()

    weather_data = []
    for city in cities:
        weather = get_weather_data(city.name)
        if weather:
            weather["id"] = city.id
            weather["background_image"] = get_local_background(weather["temperature"])
            weather_data.append(weather)

    return render_template("dashboard.html", weather_data=weather_data, message=message, message_type=message_type)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

def get_weather_data(city_name):
    api_key = os.getenv("OPENWEATHER_ACCESS_KEY")
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={api_key}&units=metric&lang=en"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        today_weather = {
            "city": data["city"]["name"],
            "temperature": data["list"][0]["main"]["temp"],
            "icon": data["list"][0]["weather"][0]["icon"],
            "description": data["list"][0]["weather"][0]["description"],
            "id": City.query.filter_by(name=city_name, user_id=current_user.id).first().id,
            "forecast": []
        }

    daily_temps = {}
    daily_icons = {}

    for item in data["list"]:
        date, time = item["dt_txt"].split(" ")
        temp = item["main"]["temp"]
    
        daily_temps.setdefault(date, []).append(temp)

        if time == "12:00:00":
            daily_icons[date] = item["weather"][0]["icon"]

    for date in daily_temps:
        if date not in daily_icons:
            hottest_item = max(
                [i for i in data["list"] if i["dt_txt"].startswith(date)],
                key=lambda x: x["main"]["temp"]
            )
            daily_icons[date] = hottest_item["weather"][0]["icon"]


    forecast_list = []

    for date, temps in daily_temps.items():
        max_temp = max(temps)
        min_temp = min(temps)

        forecast_list.append({
            "date": date,
            "max_temp": max_temp,
            "min_temp": min_temp,
            "icon": daily_icons.get(date)  
        })


    all_min = min(entry["min_temp"] for entry in forecast_list)
    all_max = max(entry["max_temp"] for entry in forecast_list)

    #ratios
    for entry in forecast_list:
        entry["bar_left"] = int(((entry["min_temp"] - all_min) / (all_max - all_min)) * 100)
        entry["bar_width"] = int(((entry["max_temp"] - entry["min_temp"]) / (all_max - all_min)) * 100)


    today_weather["forecast"] = forecast_list

    print(f"Şehir: {city_name}")
    print(f"Dönen veri: {today_weather}")
    
    return today_weather



@app.route("/send_test_mail")
@login_required
def send_test_mail():
    msg = Message(
        subject="Test Mail",
        sender=app.config['MAIL_USERNAME'],
        recipients=[current_user.email],
        body="Merhaba! Bu bir test mailidir."
    )
    mail.send(msg)
    return "Mail gönderildi!"



@app.route("/delete_city", methods=["POST"])
@login_required
def delete_city():
    city_id = request.form.get("city_id") 
    print(f"Gelen city_id: {city_id}")
    city = db.session.get(City, int(city_id))

    if not city:
        print("Şehir bulunamadı!")

    if city and city.user_id == current_user.id:
        db.session.delete(city)
        db.session.commit()
        print(f"Silinen şehir: {city.name}")


    return redirect(url_for("dashboard"))

scheduler = BackgroundScheduler()
scheduler.add_job(func=send_daily_weather_email, trigger="cron", hour = 9, minute=0)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

