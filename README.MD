# Event Detection

There are two steps to run this code:

Preprocessing: using file data_script.py and encode_window.py
You will need to have the ACE 2005 data set in the format required by this file. We cannot include the data in this release due to licence issues.

The dataset given to us is in xml format. We made major changes in the data_script.py and ed_train.py file. Contain 38 event.subtypes

Train and test the model: using file ed_train.py
# Coding environment
Python 3.6.4

numpy 1.14.2

tensorflow 1.6.0


## References:

Nguyen, Thien Huu, and Ralph Grishman. "Event Detection and Domain Adaptation with Convolutional Neural Network"

Kim, Yoon. "Convolutional neural networks for sentence classification." arXiv preprint arXiv:1408.5882 (2014).
