from main import add_dir, add_doc, clean, query_word
import os, pytest, joblib


@pytest.fixture(scope='module')
def init():
    for f in ['dac_dic.joblib', 'sant_dic.joblib', 'ward_dic.joblib']:
        if os.path.exists(f):
            os.rename(f, f.replace('joblib', 'joblib.bak'))


@pytest.fixture()
def dicts():
    # run before each test
    if not os.path.exists('doc_dic.joblib'):
        return dict(), dict(), dict()
    else:
        return joblib.load("word_dic.joblib"), joblib.load("sent_dic.joblib"), joblib.load(
            "doc_dic.joblib")


def test_empty_clean(init):
    assert not clean()


def test_add_doc(dicts):
    word_dic, sent_dic, doc_dic = dicts[0], dicts[1], dicts[2]
    assert add_doc('test_docs/doc1.txt', word_dic, sent_dic, doc_dic, save=True)[0] == 772


def test_add_doc_again(dicts):
    word_dic, sent_dic, doc_dic = dicts[0], dicts[1], dicts[2]
    assert add_doc('test_docs/doc1.txt', word_dic, sent_dic, doc_dic, save=True)[0] == -1


def test_add_dir1(dicts):
    word_dic, sent_dic, doc_dic = dicts[0], dicts[1], dicts[2]
    assert add_dir('test_docs', word_dic, sent_dic, doc_dic) == 6


def test_clean2():
    assert clean()


def test_add_dir2(dicts):
    word_dic, sent_dic, doc_dic = dicts[0], dicts[1], dicts[2]
    assert add_dir('test_docs', word_dic, sent_dic, doc_dic) == 7


def test_query_word(dicts):
    word_dic, sent_dic, doc_dic = dicts[0], dicts[1], dicts[2]
    assert query_word('government', word_dic, sent_dic, doc_dic) == 19


def test_notfound_word(dicts):
    word_dic, sent_dic, doc_dic = dicts[0], dicts[1], dicts[2]
    assert query_word('gover', word_dic, sent_dic, doc_dic) == 0


def test_clean_3():
    x = clean()
    for f in ['dac_dic.joblib', 'sant_dic.joblib', 'ward_dic.joblib']:
        if os.path.exists(f.replace('joblib','joblib.bak')):
            os.rename(f.replace('joblib', 'joblib.bak'), f)
    assert x
