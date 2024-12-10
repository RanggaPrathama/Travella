import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import random

# Load datasets
tourism = pd.read_csv(r"data\preprocessed_tourismnew.csv")
ratings = pd.read_csv(r"data\preprocessed_ratingsnew.csv")
users = pd.read_csv(r"data\preprocessed_usersnew.csv")

# Exclude columns that should not be used in the feature matrix
exclude_columns = ['Place_Id', 'Place_Name', 'Description', 'Category', 'City', 'Coordinate', 'Lat', 'Long', 'image_url']
feature_columns = [col for col in tourism.columns if col not in exclude_columns]

category_columns_encode = [col for col in feature_columns if col.startswith('Category_')]
city_columns_encode = [col for col in feature_columns if col.startswith('City_')]

tourism[category_columns_encode] *= 2
tourism[city_columns_encode] *= 1.5

# Ensure only numeric data is used in the feature matrix
#final_feature_matrix = tourism[feature_columns].select_dtypes(include=['number']).values
final_feature_matrix = tourism[feature_columns].values

# Compute cosine similarity
similarity_matrix = cosine_similarity(final_feature_matrix)
similarity_df = pd.DataFrame(similarity_matrix, index=tourism['Place_Id'], columns=tourism['Place_Id'])

# Organize recommendations by category
def organize_recommendations_by_category(recommendations):
    category_recommendations = {}
    for category in recommendations['Category'].unique():
        recs = recommendations[recommendations['Category'] == category]
        category_recommendations[category] = recs.sample(n=min(5, len(recs))).to_dict('records')  # Randomize and limit to 5 per category
    return category_recommendations

# Recommendation system function
def recommend_place(user_id, top_n=50, category=None, city=None):
    liked_places = ratings[ratings['User_Id'] == user_id].sort_values(by='Place_Ratings', ascending=False)

    if liked_places.empty:
        recommendations = tourism.copy()
        if category:
            recommendations = recommendations[recommendations['Category'] == category]
        if city:
            recommendations = recommendations[recommendations['City'] == city]
        
        subset_ids = recommendations['Place_Id']
        filtered_matrix = similarity_df.loc[subset_ids, subset_ids]
        recommendations['Cosine_Similarity'] = filtered_matrix.mean(axis=1)
        recommendations = recommendations.sort_values(by=['Cosine_Similarity', 'Rating'], ascending=[False, False]).head(top_n)
    else:
        top_place_id = liked_places.iloc[0]['Place_Id']
        similar_places = similarity_df[top_place_id].sort_values(ascending=False).head(top_n + 1)
        recommended_ids = similar_places.index[1:]
        similarity_values = similar_places[1:]
        recommendations = tourism[tourism['Place_Id'].isin(recommended_ids)].copy()
        recommendations.loc[:, 'Cosine_Similarity'] = similarity_values.values
        recommendations.loc[:, 'Cosine_Similarity'] = recommendations['Cosine_Similarity'] * 100
    
        if category:
            recommendations = recommendations[recommendations['Category'] == category]
        if city:
            recommendations = recommendations[recommendations['City'] == city]
    
    # Get top recommendations for carousel
    top_recommendations = recommendations.head(5).to_dict('records')
    
    return top_recommendations, organize_recommendations_by_category(recommendations)