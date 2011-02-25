import datetime, math, re, sqlite3, unicodedata
from fwork import *

class TopX:
    def __init__(self):
        self.dList=[]
        self.num = 0
    def step(self, val1, val2, cnt, num):
        if num=="":
            self.num = 4
        else:
            self.num = num
        if val2!="":
            self.dList.append(["-".join([val1,val2]), cnt])
        else:
            self.dList.append([val1, cnt])
    def finalize(self):
        self.dList.sort(key=lambda x:x[-1])
        dList = {}
        aList = []
        for x in [x[0] for x in self.dList]:
            if x not in dList:
                dList[x]=1
                aList.append(x)
        return "/".join(aList[:self.num])

def assignees(vers=1):
    print "Assignee %d" % vers
    if vers==1:
        conn = sqlite3.connect("assignee_1.sqlite3")
        conn.create_function("ascit",    1, ascit)
        conn.create_function("cityctry", 3, cityctry)
        c = conn.cursor()
        c.executescript("""
            PRAGMA CACHE_SIZE = 25000;
            ATTACH DATABASE 'hashTbl.sqlite3' AS hashTbl;
            ATTACH DATABASE 'assignee_v2.sqlite3' AS asg;
            DROP TABLE IF EXISTS assignee_1;
            CREATE TABLE IF NOT EXISTS assignee_1 (
                Patent VARCHAR,     AsgType INTEGER,
                Assignee VARCHAR,
                City VARCHAR,       State VARCHAR,      Country VARCHAR,
                Nationality VARCHAR,Residence VARCHAR,  AsgSeq INTEGER,

                NCity VARCHAR,      NState VARCHAR,     NCountry VARCHAR,
                NLat REAL,          NLong REAL,
                UNIQUE(Patent, AsgSeq));
            INSERT OR IGNORE INTO assignee_1
                (Patent, AsgType, Assignee, City, State, Country, Nationality, Residence, AsgSeq)
                SELECT  Patent, AsgType,
                        ascit(Assignee),
                        cityctry(City, Country, 'city'),
                        State,
                        cityctry(City, Country, 'ctry'),
                        Nationality,  Residence, AsgSeq
                  FROM  asg.assignee;
            CREATE INDEX IF NOT EXISTS asg1_uq  ON assignee_1 (Patent, AsgSeq);            
            CREATE INDEX IF NOT EXISTS asg1_loc ON assignee_1 (City, State, Country);
            INSERT OR REPLACE INTO assignee_1
                SELECT  a.Patent, a.AsgType, a.Assignee,
                        a.City, a.State, a.Country,
                        a.Nationality, a.Residence, a.AsgSeq,
                        b.NCity, b.NState, b.NCountry, b.NLat,  b.NLong
                  FROM  assignee_1 AS a
            INNER JOIN  hashTbl.locMerge AS b
                    ON  a.City=b.City AND a.State=b.State AND a.Country=b.Country AND ''=b.Zipcode;
            INSERT OR REPLACE INTO assignee_1
                SELECT  Patent, AsgType, Assignee,
                        City, State, Country,
                        Nationality, Residence, AsgSeq,
                        City, State, Country, NULL, NULL
                  FROM  assignee_1
                 WHERE  NCity IS NULL;
            CREATE INDEX IF NOT EXISTS asg1_asg ON assignee_1 (Assignee);            
            CREATE INDEX IF NOT EXISTS asg1_t   ON assignee_1 (AsgType);
            CREATE INDEX IF NOT EXISTS asg1_ps  ON assignee_1 (Patent, AsgSeq);
            CREATE INDEX IF NOT EXISTS asg1_p   ON assignee_1 (Patent);
            CREATE INDEX IF NOT EXISTS asg1_ct  ON assignee_1 (City);
            CREATE INDEX IF NOT EXISTS asg1_c   ON assignee_1 (Country);
            CREATE INDEX IF NOT EXISTS asg1_s   ON assignee_1 (State);
            CREATE INDEX IF NOT EXISTS asg1_csc ON assignee_1 (City, State, Country);
            DETACH DATABASE hashTbl;
            DETACH DATABASE asg;
            """)
        conn.commit()
        c.close()
        conn.close()
    elif vers==2:
        conn = sqlite3.connect("assignee_2.sqlite3")
        c = conn.cursor()
        c.executescript("""
            PRAGMA CACHE_SIZE = 25000;
            ATTACH DATABASE 'NBER_asg.sqlite3' AS NBER_asg;
            ATTACH DATABASE 'assignee_1.sqlite3' AS asg;
            DROP TABLE IF EXISTS assignee_2;
            CREATE TABLE IF NOT EXISTS assignee_2 (
                Patent VARCHAR,     AsgType INTEGER,
                Assignee VARCHAR,
                City VARCHAR,       State VARCHAR,      Country VARCHAR,
                Nationality VARCHAR,Residence VARCHAR,  AsgSeq INTEGER,

                NCity VARCHAR,      NState VARCHAR,     NCountry VARCHAR,
                NLat REAL,          NLong REAL,         AsgNum INTEGER,
                UNIQUE(Patent, AsgSeq));
            INSERT OR IGNORE INTO assignee_2
                (Patent, AsgType, Assignee, City, State, Country, Nationality, Residence, AsgSeq, NCity, NState, NCountry, NLat, NLong)
                SELECT  *
                  FROM  asg.assignee_1;
            CREATE INDEX IF NOT EXISTS asg2_uq  ON assignee_2 (Patent, AsgSeq);            
            INSERT OR REPLACE INTO assignee_2
                SELECT  a.*, b.pdpass
                  FROM  asg.assignee_1 AS a
            INNER JOIN  NBER_asg.main AS b
                    ON  a.assignee = b.asg
                 WHERE  b.pdpass>0;

            CREATE INDEX IF NOT EXISTS asg2_asg ON assignee_2 (Assignee);            
            CREATE INDEX IF NOT EXISTS asg2_loc ON assignee_2 (City, State, Country);
            CREATE INDEX IF NOT EXISTS asg2_t   ON assignee_2 (AsgType);
            CREATE INDEX IF NOT EXISTS asg2_ps  ON assignee_2 (Patent, AsgSeq);
            CREATE INDEX IF NOT EXISTS asg2_p   ON assignee_2 (Patent);
            CREATE INDEX IF NOT EXISTS asg2_ct  ON assignee_2 (City);
            CREATE INDEX IF NOT EXISTS asg2_c   ON assignee_2 (Country);
            CREATE INDEX IF NOT EXISTS asg2_s   ON assignee_2 (State);
            CREATE INDEX IF NOT EXISTS asg2_csc ON assignee_2 (City, State, Country);
            CREATE INDEX IF NOT EXISTS asg2_anm ON assignee_2 (AsgNum);
            DETACH DATABASE hashTbl;
            DETACH DATABASE asg;
            """)
        conn.commit()
        c.close()
        conn.close()

def classes(vers=1):
    print "Class %d" % vers
    if vers==1:
        conn = sqlite3.connect("class_1.sqlite3")
        conn.create_aggregate("TopX", 4, TopX)
        c = conn.cursor()
        c.executescript("""
            PRAGMA CACHE_SIZE = 25000;
            ATTACH DATABASE 'class.sqlite3' AS cls;
            DROP TABLE IF EXISTS class_0;
            DROP TABLE IF EXISTS class_1;
            CREATE TABLE IF NOT EXISTS class_0 (
                Patent VARCHAR, Count INTEGER,
                Class VARCHAR,  SubClass VARCHAR,
                UNIQUE(Patent, Class, SubClass));
            CREATE INDEX IF NOT EXISTS cls1_pcs ON class_0 (Patent, Class, SubClass);
            """)

        cPat = ""
        cls = []
        for x in c.execute("select * from cls.class"):
            if x[0]!=cPat:
                cnt=0
                cPat=x[0]
            cnt=cnt+1
            cls.extend([[x[0], cnt, x[2], x[3]]])

        c.executemany("INSERT OR REPLACE INTO class_0 VALUES (?, ?, ?, ?)", cls)

        c.executescript("""
            CREATE INDEX IF NOT EXISTS cls0_p  ON class_0 (Patent);
            CREATE INDEX IF NOT EXISTS cls0_c  ON class_0 (Count);
            CREATE INDEX IF NOT EXISTS cls0_m  ON class_0 (Class);
            CREATE INDEX IF NOT EXISTS cls0_ms ON class_0 (Class, SubClass);
            DETACH DATABASE cls;
            CREATE TABLE IF NOT EXISTS class_1 (
                Patent VARCHAR, Class VARCHAR, ClassSub VARCHAR,
                UNIQUE(Patent));
            CREATE INDEX IF NOT EXISTS cls1_p  ON class_1 (Patent);
            INSERT OR REPLACE INTO class_1
                SELECT  Patent,
                        TopX(Class, '', Count, 4),
                        TopX(Class, SubClass, Count, 4)
                  FROM  class_0
              GROUP BY  Patent;
            """)
        conn.commit()
        c.close()
        conn.close()

def inventors(vers=1):
    print "Inventor %d" % vers
    if vers==1:
        conn = sqlite3.connect("../sqlite/inventor_1.sqlite3")
        conn.create_function("ascit",    1, ascit)
        conn.create_function("cityctry", 3, cityctry)
        c = conn.cursor()
        c.executescript("""
            PRAGMA CACHE_SIZE = 25000;
            ATTACH DATABASE '../sqlite/hashTbl.sqlite3' AS hashTbl;
            ATTACH DATABASE '../sqlite/inventor.sqlite3' AS inv;
            DROP TABLE IF EXISTS inventor_1;
            CREATE TABLE IF NOT EXISTS inventor_1 (
                Patent VARCHAR,
                Firstname VARCHAR,  Lastname VARCHAR,
                
                Street VARCHAR,     City VARCHAR,       State VARCHAR,
                Country VARCHAR,    Zipcode VARCHAR,

                NCity VARCHAR,      NState VARCHAR,
                NCountry VARCHAR,   NZipcode VARCHAR,
                NLat REAL,          NLong REAL,                
                
                Nationality VARCHAR,
                InvSeq INTEGER,
                UNIQUE(Patent,InvSeq));
            INSERT OR IGNORE INTO inventor_1
                (Patent, Firstname, Lastname, Street, City, State, Country, Zipcode, Nationality, InvSeq)
                SELECT  Patent,
                        ascit(Firstname),
                        ascit(Lastname),
                        ascit(Street),
                        cityctry(City, Country, 'city'),
                        State,
                        cityctry(City, Country, 'ctry'),
                        UPPER(Zipcode),
                        Nationality,  InvSeq
                  FROM  inv.inventor;
            CREATE INDEX IF NOT EXISTS inv1_pti ON inventor_1 (Patent, InvSeq);
            CREATE INDEX IF NOT EXISTS inv1_loc ON inventor_1 (City, State, Country, Zipcode);
            INSERT OR REPLACE INTO inventor_1
                SELECT  a.Patent, a.Firstname, a.Lastname, a.Street, 
                        a.City,  a.State,  a.Country,  a.Zipcode,
                        b.NCity, b.NState, b.NCountry, b.NZipcode,
                        b.NLat,  b.NLong,    a.Nationality, a.InvSeq
                  FROM  inventor_1 AS a
            INNER JOIN  hashTbl.locMerge AS b
                    ON  a.City=b.City AND a.State=b.State AND a.Country=b.Country AND a.Zipcode=b.Zipcode;
            INSERT OR REPLACE INTO inventor_1
                SELECT  Patent, Firstname, Lastname, Street, 
                        City, State, Country, Zipcode,
                        City, State, Country, Zipcode,
                        NULL, NULL, Nationality, InvSeq
                  FROM  inventor_1
                 WHERE  NCity IS NULL;
            CREATE INDEX IF NOT EXISTS inv1_lcN ON inventor_1 (NCity, NState, NCountry, NZipcode);
            CREATE INDEX IF NOT EXISTS inv1_LF ON inventor_1  (Lastname, Firstname);
            CREATE INDEX IF NOT EXISTS inv1_PLF ON inventor_1  (Patent, Lastname, Firstname);
            DETACH DATABASE hashTbl;
            DETACH DATABASE inv;
            """)

        conn.commit()
        c.close()
        conn.close()

def lawyers(vers=1):
    print "Lawyer %d" % vers
    if vers==1:
        conn = sqlite3.connect("../sqlite/lawyer_1.sqlite3")
        conn.create_function("ascit",    1, ascit)
        c = conn.cursor()
        c.executescript("""
            PRAGMA CACHE_SIZE = 25000;
            ATTACH DATABASE '../sqlite/lawyer.sqlite3' AS law;
            DROP TABLE IF EXISTS lawyer_1;
            CREATE TABLE IF NOT EXISTS lawyer_1 AS
                SELECT  Patent,
                        ascit(Firstname) AS Firstname,
                        ascit(Lastname)  AS Lastname,
                        LawCountry,
                        ascit(OrgName)   AS OrgName,
                        LawSeq
                  FROM  law.lawyer;
            CREATE INDEX IF NOT EXISTS law1_p  ON lawyer_1 (Patent);
            CREATE INDEX IF NOT EXISTS law1_pl ON lawyer_1 (Patent, LawSeq);
            DETACH DATABASE law;
            """)

        conn.commit()
        c.close()
        conn.close()
