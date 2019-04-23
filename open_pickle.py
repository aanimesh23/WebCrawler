import pickle

def open_pickle(p):
    with open(p, 'rb') as f:
        data = pickle.load(f)
        print(data)


open_pickle('fetched.pkl')
open_pickle('url_queue.pkl')
open_pickle('url_set.pkl')

