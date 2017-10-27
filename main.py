import logging, argparse
import os
import gensim
import nltk
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

FNAME_SENTS = 'sent_dic.joblib'
FNAME_WORDS = 'word_dic.joblib'
FNAME_DOCS = 'docs_dic.joblib'


def add_doc(fname, word_dic, sent_dic, doc_dic, save=False):
    # adds a doc to the database

    # check if a doc has already been added
    if fname in set(doc_dic.values()):
        log.info("Document {} already added to DB".format(fname))
        return sent_dic, word_dic, doc_dic
    # Compute number of this doc
    ndoc = len(doc_dic) + 1
    # Add doc to doc_dic
    doc_dic[ndoc] = fname  #  save the fname of this doc in the docs_dic
    # Read doc
    doc = open(fname, 'r', encoding='utf-8').readlines()
    log.info('Found {} paragraphs'.format(len(doc)))
    n = 0  # counter for the number of sentence
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
                    word_dic[word] = set()
                word_dic[word] |= set([sent_index])

    log.info("Added {} words".format(n))

    if save:
        joblib.dump(word_dic, FNAME_WORDS)
        joblib.dump(sent_dic, FNAME_SENTS)
        joblib.dump(doc_dic, FNAME_DOCS)
    else:
        return sent_dic, word_dic, doc_dic


def add_dir(dirname, word_dic, sent_dic, doc_dic, nmax):

    if not dirname.endswith('/'):
        dirname += '/'
    docs = os.listdir(dirname)
    n = len(docs) if nmax is None else min(len(docs),nmax)
    print(docs)
    for ind, d in enumerate(docs[:n]):
        log.info('Reading doc {} in {} ({} of {})'.format(d, dirname, ind+1, n))
        word_dic, sent_dic, doc_dic = add_doc(dirname + d, word_dic, sent_dic, doc_dic)

    joblib.dump(word_dic, FNAME_WORDS)
    joblib.dump(sent_dic, FNAME_SENTS)
    joblib.dump(doc_dic, FNAME_DOCS)


def query_word(word, word_dic, sent_dic, doc_dic):
    if word not in word_dic:
        log.info('Word {} not found in database'.format(word))
        return
    log.debug('Word {} appearing in {}'.format(word, word_dic[word]))
    for app in word_dic[word]:
        log.info('Doc: {}'.format(doc_dic[int(app.split('_')[0])]))
        log.info(textwrap.fill(sent_dic[app],100))
        log.info('')


if __name__ == '__main__':

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
    if os.path.exists(FNAME_WORDS):
        word_dic, sent_dic, doc_dic = joblib.load(FNAME_WORDS), joblib.load(FNAME_SENTS), joblib.load(FNAME_DOCS)
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
        if os.path.exists(FNAME_WORDS):
            os.remove(FNAME_WORDS)
            os.remove(FNAME_SENTS)
            os.remove(FNAME_DOCS)
            log.info("Database cleaned")
        else:
            log.info("Nothing to clean")
