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


def add_doc(fname, cur):
    """
    adds a doc to the database
    :param fname: path to the document
    :param cur: cursor pointing to the DB
    :return number of words added
    """

    # check if file exists
    if not os.path.exists(fname):
        log.info('File {} not found'.format(fname))
        return -1

    # check if this doc has already been added
    if cur.execute("select 1 from doc_dic where fname=='{}'".format(fname)).fetchone() is not None:
        log.info('Doc {} skipped, already added'.format(fname))
        return -1

    # Add doc to doc_dic
    ndoc = cur.execute("select count(*) from doc_dic").fetchone()[0] + 1
    cur.execute("insert into doc_dic (ndoc, fname) values ({}, '{}')".format(ndoc, fname))

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
                    cur.execute("update word_dic set apps = '{}' where word = "
                                "'{}'".format(str(','.join(word_apps)), word))

    new_words = cur.execute("select count(*) from word_dic").fetchone()[0] - nwords
    log.info("Added {} new words".format(new_words))
    return new_words


def add_dir(dirname, cur, nmax=None):
    """
    Adds min(nmax,all) documents in a directory to the DB
    :param dirname: path to the directory
    :param cur: pointer to DB
    :param nmax: maximum of docs to add
    :return: number of docs added
    """
    if not dirname.endswith('/'):
        dirname += '/'
    docs = os.listdir(dirname)
    n = len(docs) if nmax is None else min(len(docs), nmax)
    done = 0
    for ind, d in enumerate(docs[:n]):
        log.info('Reading doc {} in {} ({} of {})'.format(d, dirname, ind + 1, n))
        nwords = add_doc(dirname + d, cur)
        done += min(1, nwords>=0)

    if done > 0:
        log.info("{} files added succesfully".format(len(docs[:n])))
    else:
        log.info("All files already in database".format(len(docs[:n])))
    return done


def query_word(word, cur):
    """
    Retrieve word usages from the database
    :param word: query word
    :param cur: pointer to DB
    :return: number of sentences where the words appears
    """
    word_apps = cur.execute("select * from word_dic where word == '{}'".format(word)).fetchone()
    if word_apps is None:
        log.info('Word {} not found in database'.format(word))
        return 0
    word_apps = word_apps[1].split(',')
    log.info('Word {} appearing in {} docs'.format(word, len({x.split('_')[0] for x in word_apps})))
    log.info('Word {} appearing in {} sentences: {}'.format(word, len(word_apps), word_apps))
    for app in word_apps:
        doc = cur.execute("select fname from doc_dic where ndoc == {}".format(app.split('_')[0])).fetchone()[0]
        log.info('Doc: {}'.format(doc))
        sent = cur.execute("select sent from sent_dic where id == '{}'".format(app)).fetchone()[0]
        log.info(textwrap.fill(sent, 100))
        log.info('')
    return len(word_apps)


def clean(cur, tables):
    """
    Remove tables from database
    :param cur: pointer to DB
    :return: True if done, False if no tables found
    """
    cleaned = False
    for i in ['doc_dic', 'sent_dic', 'word_dic']:
        if i in tables:
            n = cur.execute('select count(*) from {};'.format(i)).fetchall()[0][0]
            if n > 0:
                log.info("Found {} elems in {}. Deleting".format(n, i))
                cur.execute('delete from {};'.format(i))
                cleaned = True
    if cleaned:
        log.info("Database cleaned")
        return True
    else:
        log.info("Nothing to clean")
        return False


def init(cur, tables):
    """

    :param cur: pointer to DB
    :param tables: names of tables in DB
    :return: True if success, False if tables already there
    """
    commands = {'doc_dic': "create table`doc_dic` (`ndoc` INTEGER PRIMARY KEY, `fname` TEXT);",
                'sent_dic': "create table `sent_dic` (`id` TEXT PRIMARY KEY, `sent` TEXT);",
                'word_dic': "create table `word_dic` (`word` TEXT PRIMARY KEY, `apps` TEXT);"}
    new_table = False
    for i in commands.keys():
        if i not in tables:
            new_table = True
            cur.execute(commands[i])
    if new_table:
        log.info("Database succesfully initialized")
        return True
    else:
        log.info("No need to initialize, tables already present")
        return False


if __name__ == '__main__':

    # create the top-level parser
    parser = argparse.ArgumentParser(prog='PROG')
    subparsers = parser.add_subparsers(help='help for subcommand', dest='command')

    # create the parser for the "add_dir" command
    parser_a = subparsers.add_parser('add_dir')
    parser_a.add_argument('dirname', type=str, help='dir name')
    parser_a.add_argument('maxdocs', default=None, help='Max number of docs to add')

    # create the parser for the "add_doc" command
    parser_b = subparsers.add_parser('add_doc')
    parser_b.add_argument('fname', type=str, help='file name')

    parser_c = subparsers.add_parser('query_word')
    parser_c.add_argument('word', type=str)

    parser_d = subparsers.add_parser('clean')

    args = parser.parse_args()
    command = args.command
    if command is None:
        parser.print_help()
        quit()

    db = sqlite3.connect('eigen.db')
    cur = db.cursor()
    tables = cur.execute("select name from sqlite_master where type=='table'").fetchall()
    # A list of tuples is returned, turn to list
    if len(tables) > 0:
        tables = [i[0] for i in tables]

    else:  # if there are no tables
        if command in ['add_doc','add_dir']:
            init(cur, tables)
        else:
            os.remove('eigen.db')
            if command == 'clean':
                log.info("Nothing to clean")
            else:  # query word
                log.info("No data in the system. Please add data before querying")
            quit()

    if command == 'add_dir':
        try:
            maxdocs = int(args.maxdocs)
        except ValueError:
            log.info("Invalid max docs argument")
            quit()
        add_dir(args.dirname, cur, nmax=maxdocs)
    elif command == 'add_doc':
        add_doc(args.fname, cur)
    elif command == 'query_word':
        # Only query if any docs have been added
        if cur.execute('SELECT * from doc_dic').fetchone() is None:
            log.info("No docs added, cannot query words")
            quit()
        query_word(args.word, cur)
    else:  # command == 'clean':
        clean(cur, tables)

    db.commit()
