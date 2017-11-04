import argparse
import os
import textwrap
import logging
import joblib
from nltk.corpus import stopwords
from nltk import RegexpTokenizer
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

stop = set(stopwords.words('english'))

punkt_params = PunktParameters()
punkt_params.abbrev_types = set(['dr','mr','i.e','e.g'])
sent_tok = PunktSentenceTokenizer(punkt_params)
word_tok = RegexpTokenizer(r'\w+')


def add_doc(fname, word_dic, sent_dic, doc_dic, save=False):
    """
    adds a doc to the database
    :param fname: path to the document
    :param word_dic: the words dictionary
    :param sent_dic: the sentences dictionary
    :param doc_dic: the documents dictionary
    :param save: a boolean to avoid saving files to disk if we are adding 
            multiple docs (being called from add_dir)
    :return updated dicts and number of words added
    """

    # check if a doc has already been added
    if fname in set(doc_dic.values()):
        log.info("Document {} already added to DB".format(fname))
        return -1, sent_dic, word_dic, doc_dic
    # Compute number of this doc
    ndoc = len(doc_dic) + 1
    # Add doc to doc_dic
    doc_dic[ndoc] = fname  #  save the fname of this doc in the doc_dic
    # Read doc
    doc = open(fname, 'r', encoding='utf-8').readlines()
    n, w = 0, 0  # counters for the number of sentences and words
    for par in doc:  # for each paragraph split sentences
        for sent in sent_tok.tokenize(par):
            n += 1
            # doc 2, sentence 5 indexed as 2_5
            sent_index = str(ndoc) + '_' + str(n)
            sent_dic[sent_index] = sent.strip('\n')
            for word in word_tok.tokenize(sent):
                if word in stop or len(word) == 1:
                    continue
                if word not in word_dic:
                    w += 1
                    word_dic[word] = set()
                word_dic[word] |= set([sent_index])

    log.info("Added {} new words".format(w))

    if save:
        joblib.dump(word_dic, "word_dic.joblib")
        joblib.dump(sent_dic, "sent_dic.joblib")
        joblib.dump(doc_dic, "doc_dic.joblib")

    return w, sent_dic, word_dic, doc_dic


def add_dir(dirname, word_dic, sent_dic, doc_dic, nmax=None):
    """
    add all docs in directory dirname to the database
    :param dirname: path to the directory
    :param word_dic: the words dictionary
    :param sent_dic: the sentences dictionary
    :param doc_dic: the documents dictionary
    :param nmax: maximum of docs to add
    :return: None
    """

    if not dirname.endswith('/'):
        dirname += '/'
    docs = os.listdir(dirname)
    n = len(docs) if nmax is None else min(len(docs),nmax)
    done = 0
    for ind, d in enumerate(docs[:n]):
        log.info('Reading doc {} in {} ({} of {})'.format(d, dirname, ind+1, n))
        nwords, word_dic, sent_dic, doc_dic = add_doc(dirname + d, word_dic, sent_dic, doc_dic)
        done += min(1, nwords>=0)

    joblib.dump(word_dic, "word_dic.joblib")
    joblib.dump(sent_dic, "sent_dic.joblib")
    joblib.dump(doc_dic, "doc_dic.joblib")
    if done > 0:
        log.info("{} files added succesfully".format(len(docs[:n])))
    else:
        log.info("All files already in database".format(len(docs[:n])))
    return done


def query_word(word, word_dic, sent_dic, doc_dic):
    """
    query word usages to the database
    :param word: query word
    :param word_dic: the words dictionary
    :param sent_dic: the sentences dictionary
    :param doc_dic: the documents dictionary
    :return: None
    """

    if word not in word_dic:
        log.info('Word {} not found in database'.format(word))
        return 0
    log.info('Word {} appearing in {} docs'.format(word, len({x.split('_')[0] for x in word_dic[word]})))
    log.info('Word {} appearing in {} sentences: {}'.format(word, len(word_dic[word]), word_dic[word]))
    for app in word_dic[word]:
        log.info('Doc: {}'.format(doc_dic[int(app.split('_')[0])]))
        log.info(textwrap.fill(sent_dic[app],100))
        log.info('')

    return len(word_dic[word])


def clean():
    """
    Remove database, i.e. word_dic, sent_dic, and doc_dic
    :return:
    """

    cleaned = False
    files = ["word_dic.joblib", "sent_dic.joblib", "doc_dic.joblib"]
    for f in files:
        if os.path.exists(f):
            os.remove(f)
            cleaned=True
    if cleaned:
        log.info("Database cleaned")
    else:
        log.info("Nothing to clean")
    return cleaned


if __name__ == '__main__':

    # Examples:

    # python3 main.py add_dir test_docs
    # python3 main.py query_word government
    # python3 main.py query_word government
    # python3 main.py query_word governm --> Not found

    # create the top-level parser
    parser = argparse.ArgumentParser(prog='PROG')
    subparsers = parser.add_subparsers(help='help for subcommand', dest='command')

    # create the parser for the "add_dir" command
    parser_a = subparsers.add_parser('add_dir')
    parser_a.add_argument('dirname', type=str, help='dir name')
    parser_a.add_argument('-maxdocs', default=None, help='Max number of docs to add')

    # create the parser for the "add_doc" command
    parser_b = subparsers.add_parser('add_doc')
    parser_b.add_argument('fname', type=str, help='file name')

    parser_c = subparsers.add_parser('query_word')
    parser_c.add_argument('word', type=str)

    parser_d = subparsers.add_parser('clean')

    args = parser.parse_args()
    command = args.command
    if os.path.exists("word_dic.joblib"):
        word_dic, sent_dic, doc_dic = joblib.load("word_dic.joblib"), joblib.load("sent_dic.joblib"), joblib.load("doc_dic.joblib")
    else:
        if command == 'query_word':
            log.info("No docs added, cannot query words")
            quit()
        word_dic, sent_dic, doc_dic = dict(), dict(), dict()

    if command == 'add_dir':
        add_dir(args.dirname, word_dic, sent_dic, doc_dic, nmax=args.maxdocs)
    elif command == 'add_doc':
        add_doc(args.fname, word_dic, sent_dic, doc_dic, save=True)
    elif command == 'query_word':
        query_word(args.word, word_dic, sent_dic, doc_dic)
    elif command == 'clean':
        clean()
