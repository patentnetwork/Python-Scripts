#This file is meant to separate the patent related datasets by Year

import sys, datetime, os
sys.path.append("/home/ron/PythonBase")
import SQLite
import senAdd

yr = int(sys.argv[1]) #min year
src = sys.argv[2] #source directory

direc = '/home/ron/disambig/sqlite/backup'

print "Generating patent{yr}".format(yr=yr)
s = SQLite.SQLite(db='{direc}/patent{yr}'.format(direc=direc, yr=yr))
s.optimize()
for file in [x for x in os.listdir(src) if x.split(".")[1]=="sqlite3" and x.split(".")[0]!="hashTbl"]:
    print file
    s.attach('{src}/{file}'.format(src=src, file=file))
    table = file.split(".")[0]
    s.replicate(tableTo=table, table=table, db="db")
    s.addSQL(db="db", data=table, table=table)

s.close()
