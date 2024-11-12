import streamlit as st
import pandas as pd
import pickle
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import gzip

# Create a session for requests with retries on failed responses
def create_requests_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

# Fetch movie details from the API
@st.cache_data(ttl=3600)
def fetch_movie_details(movie_id):
    api_key = '5893850cacc54ee9a64e021f17606613'
    endpoint = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US'
    session = create_requests_session()
    
    try:
        response = session.get(endpoint, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Handle missing or incomplete data gracefully
        poster_path = data.get('poster_path', None)
        title = data.get('title', 'N/A')
        rating = data.get('vote_average', 'N/A')
        overview = data.get('overview', 'Information temporarily unavailable.')

        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}"
        else:
            poster_url = "https://via.placeholder.com/500x750?text=No+Image"

        return {
            'poster_url': poster_url,
            'rating': round(float(rating), 1) if isinstance(rating, (int, float)) else 'N/A',
            'overview': overview,
            'title': title
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching movie details: {e}")
        return {
            'poster_url': "https://via.placeholder.com/500x750?text=Error+Loading+Poster",
            'rating': 'N/A',
            'overview': 'Information temporarily unavailable.',
            'title': 'N/A'
        }

# Load movie data and similarity matrix
@st.cache_resource
def load_data():
    try:
        with open('movies_dict.pkl', 'rb') as f:
            movies_df = pd.DataFrame(pickle.load(f))
        with gzip.open('similarity.pkl.gz', 'rb') as f:
            similarity_matrix = pickle.load(f)
        return movies_df, similarity_matrix
    except Exception as e:
        st.error(f"Error loading movie data: {e}")
        return None, None

# Get a list of recommended movies based on the user's selection
def get_recommendations(movie_name):
    try:
        movie_index = movies[movies['title'] == movie_name].index[0]
        distances = similarity[movie_index]
        recommendations = [{'movie_id': movies.iloc[movie_index].movie_id, 'title': movies.iloc[movie_index].title}]
        recommendations += [{'movie_id': movies.iloc[index].movie_id, 'title': movies.iloc[index].title} for index, score in sorted(enumerate(distances), key=lambda x: x[1], reverse=True)[1:5]]
        return recommendations
    except IndexError:
        st.error("Error: Movie not found. Please try a different movie.")
        return []

# Create a grid to display the movie details
def create_movie_grid(movie, col, show_details):
    with col:
        details = fetch_movie_details(movie['movie_id'])
        st.image(details['poster_url'], use_container_width=True)
        st.markdown(f"**{details['title']}**")
        if show_details:
            st.markdown(f"⭐ Rating: **{details['rating']}**")
            st.caption(details['overview'][:100] + "..." if len(details['overview']) > 100 else details['overview'])

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Popular Movies", "Recommend Movies", "Contact Us"])

# Load data
movies, similarity = load_data()

# Page: Popular Movies
if page == "Popular Movies":
    st.title(" 🎬 Top 10 Popular Movies")
    if movies is not None:
        for i in range(0, 10, 5):  # Display top 10 movies in 2 rows of 5 columns
            cols = st.columns(5)
            for j, col in enumerate(cols):
                if i + j < len(movies):
                    create_movie_grid(movies.iloc[i + j], col, show_details=False)
    else:
        st.error("Unable to load movie data.")

# Page: Recommend Movies
elif page == "Recommend Movies":
    st.title('🎬 Movie Recommender System')
    st.markdown("**Get personalized movie recommendations based on your favorite movies!**")
    
    if movies is not None and similarity is not None:
        selected_movie = st.selectbox("Choose a Movie", movies['title'].values)
        if st.button('Recommend'):
            recommendations = get_recommendations(selected_movie)
            for i in range(0, len(recommendations), 5):
                cols = st.columns(5)
                for j, col in enumerate(cols):
                    if i + j < len(recommendations):
                        create_movie_grid(recommendations[i + j], col, show_details=True)
    else:
        st.error("Unable to load the movie recommender system. Please try again later.")

# Page: Contact Us
elif page == "Contact Us":
    st.title("Contact Us")
    st.write("For any inquiries or support, please contact us at pranavkonda12@gmail.com or call us at +918341469052")
