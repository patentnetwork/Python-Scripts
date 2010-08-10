#!/bin/sh
#sudo cp /home/ron/disambig/sqlite/invpatC.sqlite3 /home/ron/disambig/sqlite/invpatC.older.sqlite3
#sudo cp /home/alex/disambig/single/sqlite_dbs/invpatC.sqlite3 /home/ron/disambig/sqlite/invpatC.sqlite3
sudo cp /home/alex/disambig/single/sqlite_dbs/invpatC.v9.sqlite3 /home/ron/disambig/sqlite/invpatC.v10.sqlite3
sudo chmod 777 /home/ron/disambig/sqlite/invpatC.v10.sqlite3
#sudo cp /home/ron/disambig/sqlite/invpatC.sqlite3 /home/ron/disambig/sqlite/invpatC.copy.sqlite3
cd /home/ron/disambig/python
python compressBlk_v6.py
cd ../..
