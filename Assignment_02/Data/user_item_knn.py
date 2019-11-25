from sklearn.metrics.pairwise import cosine_similarity
import heapq
from utils import *


m_cols = ['title', 'id', 'genres', 'homepage', 'overview', 'poster_path', 'production_companies', 'popularity']


def cosSimilarityUser(data):
    # Calculate the Cosine Similarity Matrix
    user_similarity = cosine_similarity(data)

    # Preview the Similarity Matrix

    return user_similarity


def predictUser(ratings, similarity, num_items):
    # The Average Rating Values for Each User
    mean_user_rating = np.repeat(np.array([ratings.mean(axis=1)]), num_items, axis=0).T

    # The Difference Between Each Rating Value and The Average Value
    ratings_diff = ratings - mean_user_rating

    # Calculate the Predicted Score
    pred = mean_user_rating + \
           np.dot(similarity, ratings_diff) / np.array([np.abs(similarity).sum(axis=1)]).T
    return pred


def cosSimilarityItem(data):
    item_similarity = cosine_similarity(data.T)
    return item_similarity


def predictItem(ratings, similarity, num_users):
    # The Average Rating Values for Each Item
    mean_item_rating = np.repeat(np.array([ratings.mean(axis=0)]), num_users, axis=0)

    # The Difference Between Each Rating Value and The Average Value
    ratings_diff = ratings - mean_item_rating

    # Calculate the Predicted Score
    pred = mean_item_rating + \
           np.dot(ratings_diff, similarity) / np.abs(similarity).sum(axis=1)

    return pred


def recItemsForOneUser(pred_array, train_array, user, num_rec):
    # Change Training Arrary Into Sparse Matrix
    train_matrix = sp.csr_matrix(train_array)

    # Get the Item IDs in the Training Data For the Specified User
    train_items_for_user = train_matrix.getrow(user).nonzero()[1]

    # Create A Dictionary with Key-Value Pairs as ItemID-PredictedValue Pair
    pred_dict_for_user = dict(zip(np.arange(train_matrix.shape[1]), pred_array[user]))

    # Remove the Key-Value Pairs used in Training
    for iid in train_items_for_user:
        pred_dict_for_user.pop(iid)

    # Select the Top-N Items in The Sorted List
    rec_list_for_user = heapq.nlargest(num_rec, pred_dict_for_user.items(), key=lambda tup: tup[1])

    # Get the Item ID List From the Top-N Tuples
    rec_item_list = [tup[0] for tup in rec_list_for_user]
    return rec_item_list


def calMetrics(train_array, test_array, pred_array, at_K=10):
    # Get All the User IDs in Test Dataset
    test_matrix = sp.coo_matrix(test_array)
    test_users = test_matrix.row
    test_matrix = test_matrix.tocsr()

    # List to Store the Precision/Recall Value for Each User
    precision_u_at_K = []
    recall_u_at_K = []

    # Loop for Each User
    for u in test_users:
        # Get the Recommendation List for the User in Consideration
        rec_list_u = recItemsForOneUser(pred_array, train_array, u, at_K)

        # Generate a Item ID List For Testing
        item_list_u = test_matrix.getrow(u).nonzero()[1]

        # Calculate the Precision and Recall Value for this User
        precision_u, recall_u = Precision_and_Recall(rec_list_u, item_list_u)

        # Save the Precision/Recall Values
        precision_u_at_K.append(precision_u)
        recall_u_at_K.append(recall_u)

    # Calculate the Average Precision/Recall Values Over All Users


def id_to_info(recommended_ids, movie_metadata_df):
    # print(recommended_ids)
    ids = {"recommended_ids": recommended_ids}
    # print(ids)
    title_ids = pd.DataFrame(ids)
    # print(title_ids)
    title_df = pd.merge(title_ids, movie_metadata_df, left_on='recommended_ids', right_on='movie_id')
    # title_list = title_df["title"].tolist()
    print(title_df.to_string())
    return title_df


# def top_popularity(metadata_file='movies_metadata.csv'):
def top_popularity(metadata_file='./Data/movies_metadata.csv'):

    m_df = pd.read_csv(metadata_file, usecols=m_cols, low_memory=False)
    m_df['id'] = pd.to_numeric(m_df['id'], errors='coerce')
    m_df['popularity'] = pd.to_numeric(m_df['popularity'], errors='coerce')
    m_df = m_df.dropna(axis=0, how='any')
    m_df.id = m_df.id.astype(int)
    m_df = m_df.sort_values(by='popularity', ascending=False)
    return m_df.head(10)
    # print(m_df.head(10).to_string(index=False))
    # return m_df['id'].head(10).to_list()


def search_movie(movie_name, metadata_file='movies_metadata.csv'):
    m_df = pd.read_csv(metadata_file, usecols=['id', 'original_title'], low_memory=False)
    m_df['id'] = pd.to_numeric(m_df['id'], errors='coerce')
    m_df = m_df.dropna(axis=0, how='any')
    m_df.id = m_df.id.astype(int)
    m_df = m_df.loc[m_df['original_title'].str.contains(movie_name)]
    print(m_df.head(100).to_string(index=False))
    print("=" * 120)
    return m_df['id'].head(100).to_list()


# def detail_by_id(id, metadata_file='movies_metadata.csv'):
def detail_by_id(id, metadata_file='./Data/movies_metadata.csv'):
    m_df = pd.read_csv(metadata_file, low_memory=False)
    # m_df['id'] = pd.to_numeric(m_df['id'], errors='coerce')
    # m_df = m_df.dropna(axis=0, how='any')
    # m_df.id = m_df.id.astype(int)
    # print(m_df['id'])
    detail = m_df.loc[m_df['id'] == str(id)]
    print(detail.to_string())
    return detail


def recommend_user(use_id):

    # Load Rating Data
    train, test, num_users, num_items, uid_min, iid_min = loadData(test_size=0.2)
    train_array, test_array = train.toarray(), test.toarray()

    # Load Movie MetaData
    m_cols = ['movie_id', 'title', 'release_date', 'video_release_date', 'imdb_url']
    # movie_metadata_df = pd.read_csv('ml-100k.item', sep='|', names=m_cols, usecols=range(5), encoding='latin-1')
    movie_metadata_df = pd.read_csv('./Data/ml-100k.item', sep='|', names=m_cols, usecols=range(5), encoding='latin-1')
    # movie_metadata_df = movie_metadata_df[['movie_id', 'title']]

    # Similarity And Prediction Matrices (User)
    similarity_user_array = cosSimilarityUser(train_array)
    pred_user_array = predictUser(train_array, similarity_user_array, num_items)

    # Recommendation
    rec_id_list = recItemsForOneUser(pred_user_array, train_array, use_id, 10)
    print(rec_id_list)

    # Change the recommended id list into movie title list
    print("The Recommendation List for User Is: ")
    rec_title_list = id_to_info(rec_id_list, movie_metadata_df)
    print("=" * 120)
    return rec_title_list


def popular_movies():
    print("=" * 120)
    return top_popularity()

