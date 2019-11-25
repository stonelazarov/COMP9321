import pandas as pd
import numpy as np
from random import shuffle
import scipy.sparse as sp
from sklearn.model_selection import train_test_split
from ast import literal_eval
from surprise import Reader, Dataset


# def spr_loadData(datafile='ml-100k.data'):
def spr_loadData(datafile='./Data/ml-100k.data'):
    # Load the data
    reader = Reader()
    ratings = pd.read_csv(datafile, sep='\t', names=['uid', 'iid', 'ratings', 'time'])
    ratings = ratings.drop(columns='time')

    num_users, num_items = ratings['uid'].unique().shape[0], ratings['iid'].unique().shape[0]

    # 5-fold Cross Validation
    data = Dataset.load_from_df(ratings[['uid', 'iid', 'ratings']], reader)

    return data, num_users, num_items


# def loadData(test_size=0.2, datafile='ml-100k.data', header=['uid','iid','ratings','time'], sep='\t', seed=0):
def loadData(test_size=0.2, datafile='./Data/ml-100k.data', header=['uid','iid','ratings','time'], sep='\t', seed=0):
    # Read CSV File into A Pandas DataFrame
    df = pd.read_csv(datafile, header=None, names=header, sep=sep, engine='python')

    # Preview the Data
   # print("Data Preview:")
    #with pd.option_context('display.max_columns', None):
     #   print(df.head(5))
   # print("=" * 120)

    # Delete the TimeStamp Column
    df = df.drop(columns='time')
    # The Number of User and Items
    num_users, num_items = df[header[0]].unique().shape[0], df[header[1]].unique().shape[0]
    # The minimum id of user and item (because in Python array index is from 0)
    uid_min, iid_min = df['uid'].min(), df['iid'].min()

    # Train and Test Dataset Splitting
    train_df, test_df = train_test_split(np.asarray(df), test_size=test_size, random_state=seed)

    # Change the data structure into sparse matrix
    train = sp.csr_matrix((train_df[:, 2], (train_df[:, 0]-uid_min, train_df[:, 1]-iid_min)), shape=(num_users, num_items))
    test = sp.csr_matrix((test_df[:, 2], (test_df[:, 0]-uid_min, test_df[:, 1]-iid_min)), shape=(num_users, num_items))
    return train, test, num_users, num_items, uid_min, iid_min
'''
    print("Number of Users: " + str(num_users))
    print("Number of Items: " + str(num_items))
    print("=" * 120)

    print("Sample Data: " + str(train.getrow(0).toarray()))
    print("=" * 120)
'''



def Precision_and_Recall(pred_item_list, test_item_list):
    # Calculate the Number of Occurrences of Testing Item IDs in the Prediction Item ID List
    sum_relevant_item = 0
    for item in test_item_list:
        if item in pred_item_list:
            sum_relevant_item += 1

    # Calculate the Precision and Recall Value
    precision = sum_relevant_item / len(pred_item_list)
    recall = sum_relevant_item / len(test_item_list)

    return precision, recall


def matrix2list(matrix):
    coo_mat = matrix.tocoo()
    return list(coo_mat.row), list(coo_mat.col), list(coo_mat.data)

def shuffle_list(*lists):
    '''
    Shuffle a list of lists randomly
    :param lists:
    :return:
    '''
    l = list(zip(*lists))
    shuffle(l)
    return map(list, zip(*l)) # Input lists and returns lists


# Content-based RecSys
def convert_int(x):
    try:
        return int(x)
    except:
        return np.nan


def cb_loadData(metadata_file='./Data/movies_metadata.csv', links_file='./Data/links_small.csv'):
# def cb_loadData(metadata_file='movies_metadata.csv', links_file='links_small.csv'):
    m_df = pd.read_csv(metadata_file)
    m_df['genres'] = m_df['genres'].fillna('[]')\
                    .apply(literal_eval)\
                    .apply(lambda x: [i['name'] for i in x] if isinstance(x, list) else [])

    # print("Full Movie MetaData Sample:")
    # with pd.option_context('display.max_columns', None):
    #     print(m_df.head(5))
    # print("=" * 120)

    m_df['id'] = m_df['id'].apply(convert_int)

    # Small Dataset Links
    small_mdf = pd.read_csv(links_file)
    small_mdf = small_mdf[small_mdf['tmdbId'].notnull()]['tmdbId'].astype('int')

    # print(m_df[m_df['id'].isnull()])
    m_df = m_df.drop([19730, 29503, 35587])
    m_df['id'] = m_df['id'].astype('int')

    # Filter the Original Dataset into A Small Dataset
    sm_df = m_df[m_df['id'].isin(small_mdf)]
    # print("Small Movie Dataset MetaData Sample:")
    # with pd.option_context('display.max_columns', None):
    #     print(sm_df.head(5))
    # print("=" * 120)
    # print("Number of Movies: " + str(sm_df.shape[0]))
    # print("Number of Features for Each Movie: " + str(sm_df.shape[1]))
    # print("=" * 120)

    # Prepare the Data Series for All the Movies
    sm_df = sm_df.reset_index()
    titles = sm_df['title']
    movie_list = pd.Series(sm_df.index, index=titles)

   # print("Movie Title List Sample: ")
    #with pd.option_context('display.max_columns', None):
     #   print(movie_list.head(5))
    #print("=" * 120)

    return sm_df, movie_list

