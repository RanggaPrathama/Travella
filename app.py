from flask import Flask, render_template, request, flash, redirect, url_for, session
import pandas as pd
from dotenv import load_dotenv
import os
#from model import recommend_place
from modelnew import recommend_place, recomendation_by_category

app = Flask(__name__)

load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")

@app.route('/', methods= ["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"{email}, {password}")
        try:
            user = pd.read_csv('data/preprocessed_usersnew.csv')
        except FileNotFoundError:
            flash("Data pengguna tidak ditemukan. Harap periksa file user.csv.", "error")
            return render_template("index.html")
        
        user_exist = user[(user['Email'] == email) & (user['Password'] == password)]
        if not user_exist.empty:
            #idUser = user_exist.iloc[0]['User_Id']
            idUser = int(user_exist.iloc[0]['User_Id'])
            print(f"User ID: {idUser}")
           
            session['user_id'] = idUser
            
            flash(f"Login berhasil! Selamat datang, User ID: {idUser}", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Email atau password salah. Silakan coba lagi.", "error")
            return render_template("index.html")
            
    return render_template("index.html")

@app.route("/dashboard", methods=["GET"])
def dashboard():
    user_id = session.get('user_id')
    
    if not user_id:
        flash("Sesi telah berakhir. Silakan login kembali.", "error")
        return redirect(url_for('index'))
    
    # Kategori unik
    categories = [
        {"name": "Budaya", "slug": "budaya"},
        {"name": "Taman Hiburan", "slug": "taman-hiburan"},
        {"name": "Cagar Alam", "slug": "cagar-alam"},
        {"name": "Bahari", "slug": "bahari"},
        {"name": "Pusat Perbelanjaan", "slug": "pusat-perbelanjaan"},
        {"name": "Tempat Ibadah", "slug": "tempat-ibadah"},
    ]
    
    # Rekomendasi tempat
    top_recommendations, recommendations = recommend_place(user_id)
    top_recommendations = top_recommendations.to_dict('records')
    recommendations = recommendations.to_dict('records')
    
    return render_template(
        'dashboard.html',
        user_id=user_id,
        top_recommendations=top_recommendations,
        recommendations=recommendations,
        categories=categories
    )
 
@app.route('/category/<category_slug>', methods=["GET"])
def category_content(category_slug):
    user_id = session.get('user_id')
    
    if not user_id:
        flash("Sesi telah berakhir. Silakan login kembali.", "error")
        return redirect(url_for('index'))
    
    categories = [
        {"name": "Budaya", "slug": "budaya"},
        {"name": "Taman Hiburan", "slug": "taman-hiburan"},
        {"name": "Cagar Alam", "slug": "cagar-alam"},
        {"name": "Bahari", "slug": "bahari"},
        {"name": "Pusat Perbelanjaan", "slug": "pusat-perbelanjaan"},
        {"name": "Tempat Ibadah", "slug": "tempat-ibadah"},
    ]
    
    #untuk Slider 
    top_recommendations, recommendations = recommend_place(user_id)
    top_recommendations = top_recommendations.to_dict('records')
    recommendations = recommendations.to_dict('records')
    
    # Rekomendasi tempat berdasarkan kategori
    recommendations_by_category = recomendation_by_category(user_id, category=category_slug)
    recommendations_by_category = recommendations_by_category.to_dict('records')
    
    return render_template(
        'category.html',
        user_id=user_id,
        top_recommendations=top_recommendations,
        recommendations=recommendations_by_category,
        categories=categories
    )


@app.route('/logout')
def logout():
    session.clear()  
    flash("Anda telah logout.", "success")
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)

