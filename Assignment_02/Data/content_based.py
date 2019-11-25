from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import heapq
from utils import *


def tfidf_converter(df):
    # Change the NaN Values into Empty Strings
    df['tagline'] = df['tagline'].fillna('')
    # We only Use the "Overview" and "TagLine" features to Represent Each Movie
    df['description'] = df['overview'] + df['tagline']
    df['description'] = df['description'].fillna('')

    # TF-IDF Matrix
    tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), min_df=0, stop_words='english')
    tfidf_matrix = tf.fit_transform(df['description'])


    return tfidf_matrix


def cosSimilarity(matrix):
    similarity_matrix = cosine_similarity(matrix)

    return similarity_matrix


def recForOneItem(data, movie_list_df, similarity_matrix, title, num_rec):
    # Get the Indices for Each Title
    idx = movie_list_df[title]

    # Get a List of Tuples, Where Each Tuple Contains A Movie Index and The Similarity Score
    similarity_score = list(enumerate(similarity_matrix[idx]))

    # Sort the Above List of Tuples by The Similarity Score in Descendant Order
    similarity_score = heapq.nlargest(num_rec+1, similarity_score, key=lambda tup: tup[1])

    # Get the Titles of the Recommended Movies
    movie_indices = [item[0] for item in similarity_score[1:]]
    m_cols = ['title', 'id', 'genres', 'homepage', 'overview', 'poster_path', 'production_companies', 'popularity']
    return data.iloc[movie_indices][m_cols]


def find_similar_movie(movie_name):

    data, movie_list = cb_loadData()
    tfidf_matrix = tfidf_converter(data)
    similarity = cosSimilarity(tfidf_matrix)
    recommendation = recForOneItem(data, movie_list, similarity, movie_name, 10)
    print("Recommendation List:")
    print(recommendation)

    return recommendation
