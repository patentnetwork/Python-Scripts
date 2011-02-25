#This file is meant to separate the patent related datasets by Year

import sys, datetime
sys.path.append("/home/ron/PythonBase")

import SQLite
import senAdd

direc = '/home/ron/disambig/sqlite/backup'
table = 'patent'
yrRng = range(1975, 2010)

s = SQLite.SQLite(db='%s/patent2009' % direc)
tables = s.tables();
s.close()

for table in tables:
    print "Generating", table
    s = SQLite.SQLite(db='%s/%s.sqlite3' % (direc, table), tbl=table)
    s.optimize()
    for yr in yrRng:
        s.attach('%s/patent%d' % (direc, yr))
        #Only add if table exists
        if s.tables(db='db', lookup=table):
            s.addSQL(data=table, db='db', insert='IGNORE')
        print "  -", yr, datetime.datetime.now()
    s.count()
    s.close()
