Author: Marc Torrellas
Nov. 2017

********
Overview
********

The system implemented returns usages of words in a set a documents.
There have been implemented two versions:
    - Joblib version: based on dictionaries, saved in disk as joblib files
    - SQLite version: using a SQLite-based database to save the data, better in case of scaling
    or willing to run multiple jobs of the system to parallelize the task

*******************
Python requirements
*******************

Both versions:
    - Python3
    - nltk
    - pytest

Joblib version:
    - joblib

SQLite version:
    - sqlite3


*******
Syntax
*******

python3 main.py [command] [possible args]

Available commands:
    - clean
    - add_doc
    - add_dir: can set a maximum of docs to add
    - query_word


********
Examples
********

python3 main.py clean
python3 main.py add_doc test_docs/doc1.txt
python3 main.py add_dir test_docs
python3 main.py add_dir test_docs 2
python3 main.py query_word government


*******
Testing
*******

Some tests have been prepared. They can be executed by:

pytest -s tests.py

or

pytest -vs tests.py

for additional details