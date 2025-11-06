import numpy as np
import DatenLaden

def shuffle_and_split_data(data, test_ratio):
    shuffled_indices = np.random.permutation(len(data))
    test_set_size = int(len(data) * test_ratio)
    test_indices = shuffled_indices[:test_set_size]
    train_indices = shuffled_indices[test_set_size:]
    return data.iloc[train_indices], data.iloc[test_indices]


housing = DatenLaden.load_housing_data()
train_set, test_set = shuffle_and_split_data(housing, 0.2)
print (len(train_set))
print(len(test_set))