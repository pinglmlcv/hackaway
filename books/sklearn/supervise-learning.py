import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_olivetti_faces

# know your data is important
faces = fetch_olivetti_faces()
print(faces.DESCR)
print(faces.keys())
# a good habit is to check the data whether they are normalized
print(np.max(faces.data))
print(np.min(faces.data))
print(np.mean(faces.data))

# it is healthy to plot the data before any further exploration.
def print_faces(images, target, top_n):
    "set up the figure size in inches"
    fig = plt.figure(figsize=(12, 12))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1,
                        hspace=0.05, wspace=0.05)
    for i in range(top_n):
        # plot the images in a matrix of 20x20
        p = fig.add_subplot(20, 20, i+1, xticks=[], yticks=[])
        p.imshow(images[i], cmap=plt.cm.bone)
        
        # label the image with the target value
        p.text(0, 14, str(target[i]))
        p.text(0, 60, str(i))


# ==================== support vector machine
from sklearn.svm import SVC

# the most important parameter of svm is the kernel function
svc_1 = SVC(kernel='linear')

# split the data
from sklearn.cross_validation import train_test_split
X_train, X_test, y_train, y_test = train_test_split(faces.data, faces.target, 
                                                    test_size=0.25)

# implement cross validation
from sklearn.cross_validation import cross_val_score, KFold
from scipy.stats import sem

def evaluate_cross_validation(clf, X, y, K):
    # create a k-fpld cross validation iterator
    cv = KFold(len(y), K, shuffle=True, random_state=0)
    scores = cross_val_score(clf, X, y, score)
    print(scores)
    print("Mean score: {0:.3f} (+/-{1:.3f})").format(np.mean(scores), 
                                                     sem(scores)))





