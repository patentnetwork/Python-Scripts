# TODO
# create smaller unit test cases (benchmark, database)
# Why are records over & underclumped? ie. Charles Linder 7475467, Nirmala Ramanujam 7570988, Edwin L. Thomas 7799416
# Investigate "WEIRDNESS" output : Jaro-Winkler exception thrown on comparison between  and ROBERT BRUCE


import sqlite3, sys, csv, datetime;
from fwork import *;

def bmVerify(results, filepath="", outdir = ""):
        """
        Analysis function on disambiguation results, assuming that all benchmark data
        are in the large results dataset.

        Creates analysis detail csv file and prints summary information on
        over- and underclumping statistics.

        Running from the command line (make sure to set correct file paths in file)
        python bmVerify_debug.py "input filepath" "output directory" databases
        example:
        python bmVerify_debug.py /home/ysun/disambig/newcode/all/ /home/ayu/results_v2/ invpatC_NBNA.good.Jan2011 invpatC_NBYA.good.Jan2011 invpatC_YBNA.good.Jan2011

        Running interactively:
        import bmVerify_debug
        bmVerify(['final_r7', 'final_r8'], filepath="/home/ysun/disambig/newcode/all/", outdir = "/home/ayu/results_v2/")
        
        """
        for result in results:
                uqB = "invnum_N"
                tblB = "invpat"
                fileS = "/home/ayu/benchmark/DefTruth6.csv"
                fileB = filepath + "{result}.sqlite3".format(result=result)
                output = outdir + "{result}_bm6.csv".format(result=result)

                t=datetime.datetime.now()

                print "Start time: " + str(datetime.datetime.now())
                class freqUQ:
                    def __init__(self):
                        self.list=[]
                    def step(self, value):
                        self.list.append(value)
                    def finalize(self):
                        return sorted([(self.list.count(x), x) for x in set(self.list)], reverse=True)[0][1]

                #MAKE THIS SO IT CAN ATTACH SQLITE3 FOR BENCHMARK
                dataS = uniVert([x for x in csv.reader(open(fileS, "rb"))])
                #1 = Variables, 2 = Type, 3 = Format (If necessary), 4 = Matching Type
                tList = ["%s %s" % (dataS[0][i], x) for i,x in enumerate(dataS[1]) if  x != ""]

                dataS2 = [dataS[0]]
                dataS2.extend(dataS[4:])

                #Format if its necessary --> Basically for Patents..
                for i,x in enumerate(dataS[2]):
                    if x!="":
                        for j in xrange(1,len(dataS2)):
                            if dataS2[j][i].isdigit():
                                dataS2[j][i] = x % int(dataS2[j][i])

                conn = sqlite3.connect(outdir + "{detail}_bm6.sqlite3".format(detail=result)) #change back to ::memory:: if needed outdir + "{detail}_bm6.sqlite3".format(detail=result)
                conn.create_function("jarow", 2, jarow)
                conn.create_function("errD", 2, lambda x,y: (x!=y) and 1 or None)
                conn.create_aggregate("freqUQ", 1, freqUQ)
                c = conn.cursor()

                #FIGURE OUT WHICH ONES HAVE EXACT/FUZZY
                exact = [dataS[0][i] for i,x in enumerate(dataS[3]) if x.upper()[0]=="E"]
                fuzzy = [dataS[0][i] for i,x in enumerate(dataS[3]) if x.upper()[0]=="F"]
                uqS =   [dataS[0][i] for i,x in enumerate(dataS[3]) if x.upper()[0]=="U"][0]

                #CREATE INDEX, MERGE DATA BASED ON EXACTS
                print "Creating indices... " + str(datetime.datetime.now())
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
                            ON  a.uqS=b.uqS AND b.AppYearStr <= '2009' /*AND a.uqS not in (83, 85, 93)*/
                      ORDER BY  uqS, %s;

                    """ % (fBnme, uqB, exCom, exAnd, uqB, exCom))

                print "Indices Done ... " + str(datetime.datetime.now())

                #EXPORT THE RESULTS
                writer = csv.writer(open(output, "wb"), lineterminator="\n")
                writer.writerows([[x[1] for x in c.execute("PRAGMA TABLE_INFO(dataM4)")]])
                writer.writerows(c.execute("SELECT * FROM dataM4").fetchall())
                print "Printing results ..." + str(datetime.datetime.now())
                rep = [list(x) for x in c.execute("SELECT ErrUQ, uqSUB FROM dataM4")]
                orig = len([x for x in rep if x[1]!=None])
                errm = sum([int(x[0]) for x in rep if x[0]!=None])
                u = 1.0*errm/orig
                o = 1-(float(orig)/len(rep))
                recall = 1.0 - u
                print """

                RESULTS ==================

                     Original: {original}
                  New Records: {new}
                        Total: {total}

                    Overclump: {overclump} ({o:.2%})
                   Underclump: {underclump} ({u:.2%})
                    Precision: {precision:.2%}
                       Recall: {recall:.2%}
                  File Detail: {filename}
                         Time: {time}
                    Benchmark: {benchmark}
                """.format(original = orig, new = len(rep)-orig, total = len(rep), overclump = len(rep)-orig, o = o,
                           underclump = errm, u = u, recall = recall, precision = recall/(recall+o), filename = output,
                           time = datetime.datetime.now()-t, benchmark = fileS)
                c.close()
                conn.close()


if __name__ == "__main__":
    import sys
    if(sys.argv[1] == 'help' or sys.argv[1] == '?'):
        print bmVerify.__doc__

    else:
            bmVerify(sys.argv[3:], sys.argv[1], sys.argv[2])
