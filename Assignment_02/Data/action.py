from user_item_knn import *
from content_based import *


def get_userid(user_id, action):
    user_id = int(user_id)

    return user_id, action


def get_movie(movie_name, action):
    return movie_name, action


if __name__ == '__main__':
    a = 257
    b = 'The Family'
    recommend_user(a)
    find_similar_movie(b)
    popular_movies()
