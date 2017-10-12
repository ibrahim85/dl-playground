# ----------------------------------------------------------------------------
# Copyright 2014 Nervana Systems Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------
"""
Provides helpers for text-data preprocessing
"""

import numpy as np
import re
import gzip


def clean_string(string):
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " \( ", string)
    string = re.sub(r"\)", " \) ", string)
    string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip().lower()


def get_google_word2vec_W(fname, vocab, vocab_size=50000, index_from=3, verbose=1):
    f = gzip.open(fname, 'rb')
    header = f.readline()
    vocab1_size, layer1_size = map(int, header.split())
    binary_len = np.dtype('float32').itemsize * layer1_size
    vocab_size = min(len(vocab) + index_from, vocab_size)
    if verbose:
        print "loading vectors for V - {0} words with dimension D - {1}".format(vocab_size, layer1_size)
    W = np.zeros((layer1_size, vocab_size))

    found_words = {}
    for i, line in enumerate(range(vocab1_size)):
        word = []
        while True:
            ch = f.read(1)
            if ch == ' ':
                word = ''.join(word)
                break
            if ch != '\n':
                word.append(ch)
        if word in vocab:
            wrd_id = vocab[word] + index_from
            if wrd_id < vocab_size:
                W[:, wrd_id] = np.fromstring(
                    f.read(binary_len), dtype='float32')
                found_words[wrd_id] = 1
        else:
            f.read(binary_len)
    if verbose:
        print "# words with word2vec embeddings - {0}".format(len(found_words))
        print "Initializing with random vectors for remaining words"
    cnt = 0
    for wrd_id in range(vocab_size):
        if wrd_id not in found_words:
            W[:, wrd_id] = np.random.uniform(-0.25, 0.25, layer1_size)
            cnt += 1
    assert cnt + len(found_words) == vocab_size
    return W


def get_stanford_glove_W(fname, vocab):
    pass


def pad_sentences(sentences, sentence_length=None, dtype=np.int32, pad_val=0.):
    lengths = [len(sent) for sent in sentences]

    nsamples = len(sentences)
    if sentence_length is None:
        sentence_length = np.max(lengths)

    X = (np.ones((nsamples, sentence_length)) * pad_val).astype(dtype=np.int32)
    for i, sent in enumerate(sentences):
        trunc = sent[-sentence_length:]
        X[i, -len(trunc):] = trunc
    return X

def get_paddedXY(X, y, vocab_size=20000, sentence_length=100, oov=2,
                 start=1, index_from=3, seed=113, shuffle=True):

    if shuffle:
        np.random.seed(seed)
        np.random.shuffle(X)
        np.random.seed(seed)
        np.random.shuffle(y)

    if start is not None:
        X = [[start] + [w + index_from for w in x] for x in X]
    else:
        X = [[w + index_from for w in x] for x in X]

    if not vocab_size:
        vocab_size = max([max(x) for x in X])

    # word ids - pad (0), start (1), oov (2)
    if oov is not None:
        X = [[oov if w >= vocab_size else w for w in x] for x in X]
    else:
        X = [[w for w in x if w < vocab_size] for x in X]

    X = pad_sentences(X, sentence_length=sentence_length)
    y = np.array(y, dtype=np.int32).reshape((len(y), 1))

    return X, y

