#ASSUMPTION ALL BENCHMARK DATA IS IN THE LARGE DATASET

#New line, "||"
#Counts,   "++"

nl = "||" #new line, sequential data
ct = "~"
sp = "/"

import re, sqlite3, sys, csv, datetime, types, time, os;
from fwork import *;
#from TrainingSet_compress_v2 import *;
#from PatentDates_compress import *;
from minimize import *;

def isNum(x):
    return unicode(x).isdigit() and int(x) or x

class keyDict():
    def __init__(self):
        self.dict = {}
    def addKey(self, key):
        key = unicode(key)
        if key == "" or key == "None":
            return
        elif key.find(sp) == -1:
            self.addKeyDict(key)
        else:
            for x in key.split(sp):
                self.addKeyDict(x)
    def addKeyDict(self, key):
        val, cnt = key.find(ct) == -1 and (key, 1) or key.split(ct)
        cnt = int(cnt)
        if val in self.dict:
            self.dict[val] += cnt
        else:
            self.dict[val] = cnt        
    def __str__(self):
        return sp.join([ct.join([x[0], unicode(x[1])]) for x in sorted(self.dict.items(), reverse=True, key=lambda(x):x[1])])

class recCons():
    def __init__(self):
        self.list = keyDict()
    def step(self, key):
        try:
            self.list.addKey(key)
        except:
            print "recCons", key
    def finalize(self):
        return "/".join(str(self.list).split("/")[:10])  #Limited to TOP 10 only

class numRange():
    def __init__(self):
        self.minNum = 99999999
        self.maxNum = 0
    def step(self, key):
        #FOR THE DATES
        try:
            try:
                key = time.strftime("%Y%m%d", time.strptime(unicode(key), "%m/%d/%Y"))
            except:
                key = unicode(key)
            if key.find(sp) == -1:
                keyMin, keyMax = (key, key)
            else:
                keyMin, keyMax = key.split(sp)
            keyMin, keyMax = (int(keyMin), int(keyMax))
            self.minNum = keyMin < self.minNum and keyMin or self.minNum
            self.maxNum = keyMax > self.maxNum and keyMax or self.maxNum
        except:
            print "numRange", key
    def finalize(self):
        if self.minNum == self.maxNum:
            return self.minNum
        else:
            return "%d%s%d" % (self.minNum, sp, self.maxNum)

class minComb():
    def __init__(self):
        self.minVal = None
    def step(self, key, value):
        try:
            if self.minVal == None or key < self.minVal[0]: 
                self.minVal = (key, value)
        except:
            print "minComb", key
    def finalize(self):
        return self.minVal[-1]

def flt2dec(num):
    try:
        return "%d" % int(100*num)
    except:
        return num

def primStr(val, num=1): return sp.join([x.split(ct)[0] for x in val.split(sp)[:num]])
def rem_blank(a): return re.sub(" +", "", a)
#def first_i(a): return "".join(sorted([x[0] for x in a.split(" ") if len(x)>0]))
def first_i(a): return "".join([x[0] for x in a.split(" ") if len(x)>0])
def reverse(a): return a[::-1]
    
#ORIGINAL DATASET NEEDS TO BE invnum_N and invnum <-- MERGE MERGE MERGE

#STEPS
#  1. original dataset, with proper invnum_N --> UNIQUE (Patent, Inv_Seq)
#  2. copy original as invpat_1
#  3. create training sets
#  4. disambiguate
#  5. merge disambiguated with original and replace
#  6. new block --> compress, go to 3

invpats = flatten([re.findall("invpatc[.]v([0-9]+)[.]sqlite3", x, re.I) for x in os.listdir("../sqlite/")])
invpats.sort()
tNum = (int)(invpats[-1])

conn = sqlite3.connect("../sqlite/invpatC.v%s.sqlite3" % tNum)
c = conn.cursor()
conn.create_function("flt2dec",  1, flt2dec)
conn.create_function("primStr",  1, primStr)
conn.create_function("primStrX",  2, primStr)
conn.create_function("blank0", 1, rem_blank)
conn.create_function("first_i", 1, first_i)
conn.create_function("reverse", 1, reverse)
conn.create_aggregate("recCons",  1, recCons)
conn.create_aggregate("numRange", 1, numRange)
conn.create_aggregate("minComb",  2, minComb)

#IMPORTANT BUT BLOCK OFF NOW
#if tNum>1:
#    print "Minimizing invnum_%d_sort dataset" % (tNum-1), datetime.datetime.now()
#    minimize(c, tNum-1);
#    conn.commit()

#print "Processing", tNum, datetime.datetime.now()

if tNum==2:
    c.executescript("""
        CREATE TABLE IF NOT EXISTS invpat AS
            SELECT * FROM invpat_0;
        """)
    c.executescript("""
        ALTER TABLE invpat ADD COLUMN Block1 text;
        ALTER TABLE invpat ADD COLUMN Block2 text;
        ALTER TABLE invpat ADD COLUMN Block3 text;
        """)
    c.executescript("""
        CREATE INDEX IF NOT EXISTS BlkDex1   ON invpat (Block1);
        CREATE INDEX IF NOT EXISTS BlkDex2   ON invpat (Block2);
        CREATE INDEX IF NOT EXISTS BlkDex3   ON invpat (Block3);
        CREATE INDEX IF NOT EXISTS BlkDex12  ON invpat (Block1, Block2);
        CREATE INDEX IF NOT EXISTS BlkDex23  ON invpat (Block2, Block3);
        CREATE INDEX IF NOT EXISTS BlkDex13  ON invpat (Block1, Block3);
        CREATE INDEX IF NOT EXISTS BlkDex123 ON invpat (Block1, Block2, Block3);
        """)
    conn.commit()

c.executescript("""
    CREATE INDEX IF NOT EXISTS invnum0    ON invpat (invnum);
    CREATE INDEX IF NOT EXISTS invnum_N0  ON invpat (invnum_N);
    CREATE INDEX IF NOT EXISTS appyear0   ON invpat (appyearstr);
    CREATE INDEX IF NOT EXISTS gyear0     ON invpat (gyear);
    CREATE INDEX IF NOT EXISTS country0   ON invpat (country);
    """)
c.executescript("""
    CREATE INDEX IF NOT EXISTS invnum_N%s ON invpat_%s_sort (invnum_N);
    """ % (tNum-1, tNum-1))

#Everything matches -- First 5, Last 8 -- First 5, Last 8 -- remove blanks
block = [["primStr(recCons(Firstname))", "primStr(recCons(Lastname))", "''"], 
         ["substr(primStr(recCons(Firstname)),1,5)", "substr(primStr(recCons(Lastname)),1,8)", "''"],
         ["substr(primStr(recCons(blank0(Firstname))),1,5)", "substr(primStr(recCons(blank0(Lastname))),1,8)", "''"],
         ["first_i(Firstname)", "substr(primStr(recCons(blank0(Lastname))),1,5)", "''"],
         ["substr(Firstname,1,1)", "substr(primStr(recCons(blank0(Lastname))),1,5)", "''"],
         ["first_i(Firstname)", "substr(reverse(primStr(recCons(blank0(Lastname)))),1,5)", "''"],
         ["substr(Firstname,1,1)", "substr(reverse(primStr(recCons(blank0(Lastname)))),1,5)", "''"]]






#--- GOODBYE KOREANS (WEIRDNESS) + COMPRESS INVPAT ---#

##KRs = c.execute("SELECT distinct(invnum_N) FROM invpat WHERE country='KR'").fetchall()
##c.executemany("DELETE FROM invpat_%s_sort WHERE invnum=?" % (tNum-1), KRs)
##conn.commit()
##print "Bye bye Koreans", tNum, datetime.datetime.now(), c.execute("SELECT count(*) FROM invpat_%s_sort" % (tNum-1)).fetchone()

if tNum>1:
    upd = c.execute("""SELECT  invnum_N, min(invnum)
                         FROM  invpat_%s_sort
                     GROUP BY  invnum
                       HAVING  invnum_N!=min(invnum)""" % (tNum-1)).fetchall()    
    print "Update1", tNum, datetime.datetime.now()
    c.executemany("UPDATE invpat SET invnum_N=? WHERE invnum_N=?", upd)
    conn.commit()
    print "Update2", tNum, datetime.datetime.now()

#------------#

if tNum==2:
    c.execute("""UPDATE invpat SET
                  Block1=substr(firstname,1,5),
                  Block2=substr(lastname,1,8),
                  Block3='';""");
elif tNum==3: 
    c.execute("""UPDATE invpat SET
                  Block1=substr(blank0(firstname),1,5),
                  Block2=substr(blank0(lastname),1,8),
                  Block3='';""");
elif tNum==4: 
    c.execute("""UPDATE invpat SET
                  Block1=first_i(firstname),
                  Block2=substr(blank0(lastname),1,5),
                  Block3='';""");
elif tNum==5: 
    c.execute("""UPDATE invpat SET
                  Block1=substr(firstname,1,1),
                  Block2=substr(blank0(lastname),1,5),
                  Block3='';""");
elif tNum==6: 
    c.execute("""UPDATE invpat SET
                  Block1=first_i(firstname),
                  Block2=substr(reverse(blank0(lastname)),1,5),
                  Block3='';""");
elif tNum==7: 
    c.execute("""UPDATE invpat SET
                  Block1=substr(firstname,1,1),
                  Block2=substr(reverse(blank0(lastname)),1,5),
                  Block3='';""");
elif tNum==8:
    c.execute("""UPDATE invpat SET
                  Block1=invnum_N,
                  Block2='',
                  Block3='',
                  invnum_N=invnum;""");
    
conn.commit()
print "Blocks", tNum, datetime.datetime.now(), c.execute("SELECT count(*) FROM invpat_%s_sort" % (tNum-1)).fetchone()

#------------#

c.executescript("""
    DROP TABLE IF EXISTS invpat_%d_sort;
    DROP TABLE IF EXISTS invpat_%d_sort;
    DROP TABLE IF EXISTS invpat_%d_sing;
    DROP TABLE IF EXISTS invpat_%d_sing;
    """ % (tNum-1, tNum, tNum-1, tNum))

if tNum==8:
    c.executescript("""
        CREATE TABLE IF NOT EXISTS invpat_%d_sort AS
            SELECT  recCons(Firstname) as Firstname, recCons(Lastname) as Lastname, recCons(Street) as Street, recCons(City) as City,
                    recCons(State) as State, recCons(Country) as Country, recCons(Zipcode) as Zipcode, recCons(flt2dec(Lat)) as Lat,
                    recCons(flt2dec(Lon)) as Lon, minComb(Patent, InvSeq) as InvSeq, min(Patent) as Patent, numRange(AppDateStr) as AppDateStr,
                    GYear, recCons(Assignee) as Assignee, recCons(AsgNum) as AsgNum, recCons(Class) as Class, recCons(coauths) as coauths,
                    count(*) as cnt, invnum_N, invnum, Block1, Block2, Block3
              FROM  invpat
          GROUP BY  invnum_N
            HAVING  invnum_N=invnum;
        """ % (tNum))      
    print "  -", "Created invpat_%d" % tNum, "Recs:", c.execute("select count(*) from invpat_%d_sort" % tNum).fetchone()[0], datetime.datetime.now()
    conn.commit()

elif tNum>=9:
    c.executescript("""
        CREATE TABLE IF NOT EXISTS invpat_%d_sort AS
            SELECT  recCons(Firstname) as Firstname, recCons(Lastname) as Lastname, recCons(Street) as Street, recCons(City) as City,
                    recCons(State) as State, recCons(Country) as Country, recCons(Zipcode) as Zipcode, recCons(flt2dec(Lat)) as Lat,
                    recCons(flt2dec(Lon)) as Lon, minComb(Patent, InvSeq) as InvSeq, min(Patent) as Patent, numRange(AppDateStr) as AppDateStr,
                    GYear, recCons(Assignee) as Assignee, recCons(AsgNum) as AsgNum, recCons(Class) as Class, recCons(coauths) as coauths,
                    count(*) as cnt, invnum_N, invnum, Block1, Block2, Block3
              FROM  invpat
          GROUP BY  invnum_N;
        """ % (tNum))
    print "  -", "Created invpat_%d" % tNum, "Recs:", c.execute("select count(*) from invpat_%d_sort" % tNum).fetchone()[0], datetime.datetime.now()
    conn.commit()

else:
    blocks = block[tNum-1];
    #for now, remove Koreans, Japanese, Chinese, etc
    c.executescript("""
        CREATE TABLE IF NOT EXISTS invpat_%d_sort AS
            SELECT  recCons(Firstname) as Firstname, recCons(Lastname) as Lastname, recCons(Street) as Street, recCons(City) as City,
                    recCons(State) as State, recCons(Country) as Country, recCons(Zipcode) as Zipcode, recCons(flt2dec(Lat)) as Lat,
                    recCons(flt2dec(Lon)) as Lon, minComb(Patent, InvSeq) as InvSeq, min(Patent) as Patent, numRange(AppDateStr) as AppDateStr,
                    GYear, recCons(Assignee) as Assignee, recCons(AsgNum) as AsgNum, recCons(Class) as Class, recCons(coauths) as coauths,
                    count(*) as cnt, invnum_N, invnum, %s as Block1, %s as Block2, %s as Block3
              FROM  invpat
          GROUP BY  invnum_N
            HAVING  country not in("KR", "CN", "TW", "JP");
        """ % (tNum, blocks[0], blocks[1], blocks[2]))
        
    print "  -", "Created invpat_%d" % tNum, "Recs:", c.execute("select count(*) from invpat_%d_sort" % tNum).fetchone()[0], datetime.datetime.now()
    conn.commit()

c.executescript("""
    CREATE UNIQUE INDEX IF NOT EXISTS uqINV%d ON invpat_%d_sort (Patent, InvSeq);
    REPLACE INTO invpat_%d_sort
        SELECT  Firstname, Lastname, Street, City, State, Country, Zipcode, Lat, Lon, InvSeq, Patent,
                AppDateStr, GYear, Assignee, AsgNum, Class, coauths, cnt, invnum_N, invnum, Block1, Block2, Block3
          FROM  invpat_%d_sort
      ORDER BY  Block1, Block2, Block3;
    UPDATE invpat_%d_sort SET invnum=invnum_N;
    """ % (tNum, tNum, tNum, tNum, tNum))
print "  -", "Reordered/Updated invpat_%d_sort" % tNum, "Recs:", c.execute("select count(*) from invpat_%d_sort" % tNum).fetchone()[0], datetime.datetime.now()
conn.commit()

c.executescript("""
    CREATE INDEX IF NOT EXISTS invnum%d  ON invpat_%d_sort (invnum);
    CREATE INDEX IF NOT EXISTS invnumN%d ON invpat_%d_sort (invnum_N);
    CREATE INDEX IF NOT EXISTS maxcnt%d ON invpat_%d_sort (cnt);
    """ % ((tNum, ) * 6))
print "  -", "Remaining Indexes", datetime.datetime.now()
conn.commit()

c.executescript("""
    DROP INDEX IF EXISTS Blk123;
    DROP INDEX IF EXISTS BlkDex1;
    DROP INDEX IF EXISTS BlkDex2;
    DROP INDEX IF EXISTS BlkDex3;
    DROP INDEX IF EXISTS BlkDex12;
    DROP INDEX IF EXISTS BlkDex23;
    DROP INDEX IF EXISTS BlkDex13;
    DROP INDEX IF EXISTS BlkDex123;
    """)
print "  -", "Removed unnecessary Indexes", datetime.datetime.now()
conn.commit()

c.close()
conn.close()
