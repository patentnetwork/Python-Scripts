#ASSUMPTION ALL BENCHMARK DATA IS IN THE LARGE DATASET

import sqlite3, sys, csv, datetime;
from fwork import *;

#ASSUMPTIONS
#----------------
deffileS  = "../BM/DefTruth3.csv" #REQUIRED
deffileB  = "../BM/BMData.csv"   #REQUIRED: CAN BE CSV/SQLITE3, ETC
                              #ASSUMED MAIN TABLE = FILENAME (less extension)
                              #ASSUMED NOT .csv = SQLITE3 DATABASE
#fileB  = "dataB.sqlite3"
uqB    = "invnum_N"     #USER DEFINES THIS, PATENT DATABASE, DEFAULT=INVNUM_N
output = "test.csv"     #OPTIONAL
#----------------
print """
Pre-Indexing the Base Data by:
  - Unique Fields
  - Exact matching Fields

will show improvement for the results.
"""

##UNCOMMENT THIS LATER
##fileS = raw_input("Benchmark: ")
##fileB = raw_input("Base data: ")
##tblB = raw_input("Table name (optional): ")
##uqB   = raw_input("Base Unique Key (invnum_N): ")
##output = raw_input("File output (test.csv): ")
##if fileS=="": fileS = deffileS
##if fileB=="": fileB = deffileB
##if uqB=="": uqB = "invnum_N"
##if output=="": output = "test.csv"

#DELETE THIS SOON
uqB = "invnum_N"
tblB = "invpat"
fileS = "../BM/DefTruth3.csv"
fileB = "../sqlite/invpatC.v10.sqlite3"
#fileB = "../BM/BMData.csv"
output = "test.v10.csv"
#####

##subR  = raw_input("Matched report (N): ")
#----------------
t=datetime.datetime.now()

class freqUQ:
    def __init__(self):
        self.list=[]
    def step(self, value):
        self.list.append(value)
    def finalize(self):
        return sorted([(self.list.count(x), x) for x in set(self.list)], reverse=True)[0][1]

#MAKE THIS SO IT CAN ATTACH SQLITE3 FOR BENCHMARK
dataS = uniVert([x for x in csv.reader(open("%s" % fileS, "rb"))])
#1 = Variables, 2 = Type, 3 = Format (If necessary), 4 = Matching Type
tList = ["%s %s" % (dataS[0][i], x) for i,x in enumerate(dataS[1]) if  x != ""]

dataS2 = [dataS[0]]
dataS2.extend(dataS[4:])

#Format if its necessary --> Basically for Patents..
for i,x in enumerate(dataS[2]):
    if x!="":
        for j in xrange(1,len(dataS2)):
            if dataS2[j][i].isdigit():
                exec('dataS2[j][i] = "%s" %% int(dataS2[j][i])' % x)

conn = sqlite3.connect(":memory:")
conn.create_function("jarow", 2, jarow)
conn.create_function("errD", 2, lambda x,y: (x!=y) and 1 or None)
conn.create_aggregate("freqUQ", 1, freqUQ)
c = conn.cursor()

#FIGURE OUT WHICH ONES HAVE EXACT/FUZZY
exact = [dataS[0][i] for i,x in enumerate(dataS[3]) if x.upper()[0]=="E"]
fuzzy = [dataS[0][i] for i,x in enumerate(dataS[3]) if x.upper()[0]=="F"]
uqS =   [dataS[0][i] for i,x in enumerate(dataS[3]) if x.upper()[0]=="U"][0]

#CREATE INDEX, MERGE DATA BASED ON EXACTS
exAnd = " AND ".join(["a.%s=b.%s" % (x, x) for x in exact])
exCom = ", ".join(exact)

if fileB.split(".")[-1].lower()=="csv":
    dataB = uniVert([x for x in csv.reader(open("%s" % fileB, "rb"))])
    quickSQL(c, data=dataB,  table="dataB", header=True, typeList=["Patent VARCHAR"])
    c.execute("CREATE INDEX IF NOT EXISTS dB_E ON dataB (%s)" % exCom)
    c.execute("CREATE INDEX IF NOT EXISTS dB_U ON dataB (%s)" % uqB)
    fBnme = "dataB"
else:
    c.execute("ATTACH DATABASE '%s' AS db" % fileB)
    if tblB=="":
        fBnme = "db.%s" % fileB.split(".")[-2].split("/")[-1]
    else:
        fBnme = "db.%s" % tblB

quickSQL(c, data=dataS2, table="dataS", header=True, typeList=tList)

if fuzzy:
    c.execute("CREATE INDEX IF NOT EXISTS dS_E ON dataS (%s);" % (exCom))
    c.executescript("""
        CREATE INDEX IF NOT EXISTS dS_E ON dataS (%s);

        /* RETAIN ONLY JARO>0.9 FUZZY AND EXACT MATCHES */
        CREATE TABLE dataM AS
            SELECT  a.*, %s AS uqB, %s AS uqS, %s AS jaro
              FROM  %s AS a
        INNER JOIN  dataS AS b
                ON  %s
             WHERE  jaro>0.90;

        /* DETERMINE MAXIMUM JARO FOR EACH UQ AND EXACT COMBO */
        CREATE TABLE dataT AS
            SELECT  uqS, %s, MAX(jaro) AS jaro, count(*) as cnt
              FROM  dataM
          GROUP BY  uqS, %s;

        /* RETAIN ONLY MAXIMUM JARO */
        CREATE TABLE dataM2 AS
            SELECT  a.*
              FROM  dataM AS a
        INNER JOIN  dataT AS b
                ON  a.uqS=b.uqS AND a.jaro=b.jaro AND %s;
        """ % (exCom, uqB, uqS, 
               "*".join(["jarow(a.%s, b.%s)" % (x,x) for x in fuzzy]),
               fBnme, exAnd, exCom, exCom, exAnd))
else:
    c.executescript("""
        CREATE INDEX IF NOT EXISTS dS_E ON dataS (%s);
        CREATE TABLE dataM2 AS
            SELECT  *, %s AS uqB, %s AS uqS
              FROM  %s AS a
        INNER JOIN  dataS AS b
                ON  %s;
        """ % (exCom, uqB, uqS, fBnme, exAnd))

c.executescript("""
    /* EXPAND UNIQUE BASE AND INDICATE ACTIVE MATCHES */
    CREATE TABLE dataM3 AS
        SELECT  uqS, a.*
          FROM (SELECT  uqS AS uqSUB, a.*
                  FROM (SELECT  uqB, b.*
                          FROM  (SELECT DISTINCT(uqB) FROM dataM2 WHERE uqB!="") AS a
                    INNER JOIN  %s AS b
                            ON  a.uqB=b.%s) AS a
             LEFT JOIN (SELECT %s, uqB, uqS FROM dataM2) AS b
                    ON  a.uqB=b.uqB AND %s) AS a
    INNER JOIN (SELECT DISTINCT uqB, uqS FROM dataM2) AS b
            ON  a.%s=b.uqB;

    /* INDICATE INVENTORS WHO DO NOT MATCH */
    CREATE TABLE dataM4 AS
        SELECT  errD(a.ErrUQ, uqB) AS ErrUQ, b.*
          FROM (SELECT uqS, freqUQ(uqB) as ErrUQ FROM dataM3 GROUP BY uqS) AS a
    INNER JOIN  dataM3 AS b
            ON  a.uqS=b.uqS
      ORDER BY  uqS, %s;

    """ % (fBnme, uqB, exCom, exAnd, uqB, exCom))

#EXPORT THE RESULTS
writer = csv.writer(open(output, "wb"), lineterminator="\n")
writer.writerows([[x[1] for x in c.execute("PRAGMA TABLE_INFO(dataM4)")]])
writer.writerows(c.execute("SELECT * FROM dataM4").fetchall())

##if subR!="":
##    writer = csv.writer(open("%s_sub.%s" % tuple(output.split(".")), "wb"), lineterminator="\n")
##    writer.writerows([[x[1] for x in c.execute("PRAGMA TABLE_INFO(dataM4)")]])
##    writer.writerows(c.execute("SELECT * FROM dataM4 WHERE uqSub IS NOT NULL").fetchall())

rep = [list(x) for x in c.execute("SELECT ErrUQ, uqSUB FROM dataM4")]
orig = len([x for x in rep if x[1]!=None])
errm = sum([int(x[0]) for x in rep if x[0]!=None])
print """

RESULTS ==================

     Original: %d
  New Records: %d
        Total: %d

   Undermatch: %d (%.1f%%)
  File Detail: %s
         Time: %s
""" % (orig, len(rep)-orig, len(rep), errm, 1000*errm/orig/10., output, datetime.datetime.now()-t)
c.close()
conn.close()

##if __name__=="__main__":
##    try:
##        print sys.argv[1]
##        print sys.argv[2]
##    except:
##        print "Usage: %s <query string>" % sys.argv[0]
##        raise
