import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# === 1. Load preprocessed dataset ===
tourism = pd.read_csv("data/preprocessed_tourismnew.csv")
ratings = pd.read_csv("data/preprocessed_ratingsnew.csv")
#ratings = pd.read_csv("data/tourism_rating.csv")
users = pd.read_csv("data/preprocessed_usersnew.csv")

#  dataset asli
tourism_original = pd.read_csv("data/tourism_with_id.csv")

original_min = tourism_original['Rating'].min()
original_max = tourism_original['Rating'].max()



# === 2. Pisahkan Fitur untuk Rekomendasi ===
# Ambil semua kolom fitur kecuali kolom ID dan kolom non-fitur dengan fitur2 dari pengolahan tf idf dan encoding kategori dan kota
exclude_columns = ['Place_Id', 'Place_Name', 'Description', 'Category', 'City', 'Coordinate', 'Lat', 'Long', 'image_url']
feature_columns = [col for col in tourism.columns if col not in exclude_columns]


#print(feature_columns)
final_feature_matrix = tourism[feature_columns].values

# === 3. Hitung Kesamaan ===
similarity_matrix = cosine_similarity(final_feature_matrix)

# Simpan hasil kesamaan dalam DataFrame
similarity_df = pd.DataFrame(similarity_matrix, index=tourism['Place_Id'], columns=tourism['Place_Id'])
#print(similarity_df)


# Fungsi untuk melakukan denormalisasi nilai rating
def denormalize_rating(rating, min_rating, max_rating):
    if pd.isna(rating):
        return min_rating  
    return (rating * (max_rating - min_rating)) + min_rating


#Ini untuk halaman dashboard untuk utama sendiri rekomendasi berdasarkan rating terbesar dari user
def recommend_place(user_id, top_n=10, category=None, city=None):
    # Ambil tempat wisata yang disukai pengguna
    liked_places = ratings[ratings['User_Id'] == user_id].sort_values(by='Place_Ratings', ascending=False)
    
    # Jika pengguna belum memberi rating
    if liked_places.empty:
        print("Pengguna belum memberi rating. Menggunakan fallback berbasis kesamaan.")
        return get_recommendations(category=category, city=city, top_n=top_n)
    
    # Ambil ID tempat wisata dengan rating tertinggi
    top_place_id = liked_places.iloc[0]['Place_Id']
    top_place_info = tourism[tourism['Place_Id'] == top_place_id].copy()
    top_place_info['Denormalized_Rating'] = top_place_info['Rating'].apply(
        lambda x: denormalize_rating(x, original_min, original_max)
    )
    top_place_info['Cosine_Similarity'] = 100  # Tempat favorit pengguna
    
    # Dapatkan rekomendasi
    recommendations = get_recommendations(top_place_id=top_place_id, category=category, city=city, top_n=top_n)
    
    # Tempat wisata yang disukai di posisi awal
    recommendations = pd.concat([top_place_info, recommendations], ignore_index=True).drop_duplicates(subset='Place_Id')
    recommendations.sort_values(by=['Cosine_Similarity', 'Rating'], ascending=[False, False]).head(top_n)
    
    #  slider bozz
    slider_recommendations = recommendations.head(5)
    
    
  
        
    
    return slider_recommendations[['Place_Id', 'Place_Name', 'Category', 'City', 'Rating','Denormalized_Rating', 'Cosine_Similarity', 'image_url']],recommendations[['Place_Id', 'Place_Name', 'Category', 'City', 'Rating', 'Denormalized_Rating', 'Cosine_Similarity', 'image_url']]


# Ini untuk halaman dashboard untuk rekomendasi berdasarkan kategori
def recomendation_by_category(user_id, top_n=10, category=None, city=None):
    # Ambil tempat wisata yang disukai pengguna
    liked_places = ratings[ratings['User_Id'] == user_id].sort_values(by='Place_Ratings', ascending=False)
    
    # Jika pengguna belum memberi rating
    if liked_places.empty:
        print("Pengguna belum memberi rating. Menggunakan fallback berbasis kesamaan.")
        return get_recommendations(category=category, city=city, top_n=top_n)
    
    # Ambil ID tempat wisata dengan rating tertinggi
    top_place_id = liked_places.iloc[0]['Place_Id']
    
    # Dapatkan rekomendasi tanpa memasukkan tempat wisata favorit di awal
    return get_recommendations(top_place_id=top_place_id, category=category, city=city, top_n=top_n)


def get_recommendations(top_place_id=None, category=None, city=None, top_n=10):
    if top_place_id:
        # Ambil tempat wisata yang mirip berdasarkan cosine similarity
        similar_places = similarity_df[top_place_id].sort_values(ascending=False).head(top_n + 1)
        recommended_ids = similar_places.index[1:]  # Skip tempat wisata yang sama
        similarity_values = similar_places[1:]  # Ambil nilai similarity
        
        # Tampilkan rekomendasi
        recommendations = tourism[tourism['Place_Id'].isin(recommended_ids)].copy()
        recommendations.loc[:, 'Cosine_Similarity'] = similarity_values.values
        recommendations.loc[:, 'Cosine_Similarity'] = recommendations['Cosine_Similarity'] * 100  # Persentase
    else:
        # Jika tidak ada top_place_id, gunakan fallback berbasis kesamaan global
        recommendations = tourism.copy()
        if category:
            category_col = f"Category_{category.replace(' ', '_')}"
            recommendations = recommendations[recommendations[category_col] == 1]
        if city:
            city_col = f"City_{city.replace(' ', '_')}"
            recommendations = recommendations[recommendations[city_col] == 1]
        subset_ids = recommendations['Place_Id']
        filtered_matrix = similarity_df.loc[subset_ids, subset_ids]
        recommendations['Cosine_Similarity'] = filtered_matrix.mean(axis=1)
    
    # Filter berdasarkan kategori dan kota
    if category:
        category_col = f"Category_{category.replace(' ', '_')}"
        recommendations = recommendations[recommendations[category_col] == 1]
    if city:
        city_col = f"City_{city.replace(' ', '_')}"
        recommendations = recommendations[recommendations[city_col] == 1]
    
    # Jika tidak ada hasil setelah filter, gunakan fallback global
    if recommendations.empty:
        print("Tidak ada hasil yang cocok dengan filter. Menggunakan fallback berbasis kesamaan.")
        recommendations = tourism.copy()
        if category:
            category_col = f"Category_{category.replace(' ', '_')}"
            recommendations = recommendations[recommendations[category_col] == 1]
        if city:
            city_col = f"City_{city.replace(' ', '_')}"
            recommendations = recommendations[recommendations[city_col] == 1]
        subset_ids = recommendations['Place_Id']
        filtered_matrix = similarity_df.loc[subset_ids, subset_ids]
        recommendations['Cosine_Similarity'] = filtered_matrix.mean(axis=1)
        recommendations = recommendations.sort_values(by=['Cosine_Similarity', 'Rating'], ascending=[False, False]).head(top_n)
    
     #Denormalisasi rating
    recommendations['Denormalized_Rating'] = recommendations['Rating'].apply(
        lambda x: denormalize_rating(x, original_min, original_max)
    )
    
    recommendations = recommendations.drop_duplicates(subset='Place_Id', keep='first')
    
    # Sort berdasarkan cosine similarity dan rating
    recommendations = recommendations.sort_values(by=['Cosine_Similarity', 'Rating'], ascending=[False, False]).head(top_n)
    return recommendations[['Place_Id', 'Place_Name', 'Category', 'City', 'Rating','Denormalized_Rating' ,'Cosine_Similarity', 'image_url']]


#recomendation = recommend_place(user_id = 2)
# recomendation = recomendation_by_category(user_id=2, category='Taman Hiburan')
# print(recomendation)
