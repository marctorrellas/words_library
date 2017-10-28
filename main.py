import argparse
import os
import textwrap
import logging
from nltk.corpus import stopwords
from nltk import RegexpTokenizer
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
import sqlite3

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

stop = set(stopwords.words('english'))

punkt_params = PunktParameters()
punkt_params.abbrev_types = set(['dr', 'mr', 'i.e', 'e.g'])
sent_tok = PunktSentenceTokenizer(punkt_params)
word_tok = RegexpTokenizer(r'\w+')

DB_NAME = 'eigen.db'


def add_doc(fname, cur):

    # check if this doc has already been added
    if cur.execute("select 1 from docs_dic where fname=='{}'".format(fname)).fetchone() is not None:
        log.info('Doc {} skipped, already added'.format(fname))
        return

    # Add doc to docs_dic
    ndoc = cur.execute("select count(*) from docs_dic").fetchone()[0] + 1
    cur.execute("insert into docs_dic (ndoc, fname) values ({}, '{}')".format(ndoc, fname))

    # Read doc
    doc = open(fname, 'r', encoding='utf-8').readlines()
    log.info('Found {} paragraphs'.format(len(doc)))
    n = 0  # counter for the number of sentences
    nwords = cur.execute("select count(*) from word_dic").fetchone()[0]
    for par in doc:  # for each paragraph split sentences
        for sent in sent_tok.tokenize(par):
            n += 1
            # doc 2, sentence 5 indexed as 2_5
            sent_index = str(ndoc) + '_' + str(n)
            # Add sentence to sent table
            cur.execute("insert into sent_dic (id, sent) values ('{}', '{}');".format(sent_index,
                                                                                      sent.strip('\n').
                                                                                      replace("'","''").
                                                                                      replace('"','""')))
            for word in word_tok.tokenize(sent):
                if word in stop or len(word) == 1:
                    continue
                word_apps = cur.execute('select * from word_dic where word == "{}"'.format(word)).fetchone()
                if word_apps is None:
                    cur.execute('insert into word_dic (word, apps) values ("{}", "{}")'.format(word,sent_index))
                else:
                    word_apps = set(word_apps[1].split(','))
                    word_apps |= set([sent_index])
                    cur.execute("update word_dic set apps = '{}' where word = '{}'".format(str(','.join(word_apps)),
                                                                                           word))


    # review in the other branch if this is words or sentences
    new_words = cur.execute("select count(*) from word_dic").fetchone()[0] - nwords
    log.info("Added {} words".format(new_words))


def add_dir(dirname, cur, nmax):
    if not dirname.endswith('/'):
        dirname += '/'
    docs = os.listdir(dirname)
    n = len(docs) if nmax is None else min(len(docs), nmax)
    for ind, d in enumerate(docs[:n]):
        log.info('Reading doc {} in {} ({} of {})'.format(d, dirname, ind + 1, n))
        add_doc(dirname + d, cur)


def query_word(word, cur):
    word_apps = cur.execute("select * from word_dic where word == '{}'".format(word)).fetchone()
    if word_apps is None:
        log.info('Word {} not found in database'.format(word))
        return
    word_apps = word_apps[1].split(',')
    log.info('Word {} appearing in {} docs'.format(word, len({x.split('_')[0] for x in word_apps})))
    log.debug('Word {} appearing in {}'.format(word, word_apps))
    for app in word_apps:
        doc = cur.execute("select fname from docs_dic where ndoc == {}".format(app.split('_')[0])).fetchone()[0]
        log.info('Doc: {}'.format(doc))
        sent = cur.execute("select sent from sent_dic where id == '{}'".format(app)).fetchone()[0]
        log.info(textwrap.fill(sent, 100))
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

    subparsers.add_parser('clean')
    subparsers.add_parser('init')
    subparsers.add_parser('rmall')

    args = parser.parse_args()
    command = args.command

    db = sqlite3.connect(DB_NAME)
    cur = db.cursor()
    tables = cur.execute("select name from sqlite_master where type=='table'").fetchall()

    if command == 'init':
        if len(tables) == 0:
            cur.execute("create table`docs_dic` (`ndoc` INTEGER PRIMARY KEY, `fname` TEXT);")
            cur.execute("create table `sent_dic` (`id` TEXT PRIMARY KEY, `sent` TEXT);")
            cur.execute("create table `word_dic` (`word` TEXT PRIMARY KEY, `apps` TEXT);")
            log.info("Database succesfully initialized")
            db.commit()
            quit()
        else:
            log.info("No need to initialize, tables already present")
            quit()
    elif len(tables) == 0:
        log.info("Please init the system first")
        quit()
    else:
        if command == 'add_dir':
            add_dir(args.dirname, cur, nmax=args.maxdocs)
        elif command == 'add_doc':
            add_doc(args.fname, cur)
        elif command == 'query_word':
            # Only query if any docs have been added
            if cur.execute('SELECT * from docs_dic').fetchone() is None:
                log.info("No docs added, cannot query words")
                quit()
            query_word(args.word, cur)
        else: # command == 'clean':
            if cur.execute("select * from docs_dic").fetchone() is not None:
                for i in ['docs_dic', 'sent_dic', 'word_dic']:
                    cur.execute('delete from {};'.format(i))
                log.info("Database cleaned")
            else:
                log.info("Nothing to clean")

    db.commit()
