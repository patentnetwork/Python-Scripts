#This file is meant to separate the patent related datasets by Year

import sys, datetime, os
sys.path.append("/home/ron/PythonBase")

yr0 = int(sys.argv[1])
yr1 = int(sys.argv[2])

import SQLite
import senAdd

input =  '/media/data/ron/disambig/backup'
output = '/media/data/ron/disambig/fullset'
table = 'patent'
yrRng = range(yr0, yr1+1)

s = SQLite.SQLite(db='%s/patent%d' % (input, yr1))
tables = s.tables();
s.close()

for table in tables:
    if os.path.exists('%s/%s.sqlite3' % (output, table)):
        print "Appends", table
        s = SQLite.SQLite(db='%s/%s.sqlite3' % (output, table), tbl=table)
        s.optimize()
        for yr in yrRng:
            s.attach('%s/patent%d' % (input, yr))
            if s.tables(db='db', lookup=table):
                s.addSQL(data=table, db='db', insert='IGNORE')
            print "  -", yr, datetime.datetime.now()
        s.count()
        s.close()
