import datetime

def minimize(c, num):
    c.executescript("""
        CREATE TEMPORARY TABLE invnumS AS
            SELECT invnum, invnum_N FROM invpat_%d_sort;
        CREATE INDEX invnum1  ON invnumS (invnum);
        CREATE INDEX invnumN1 ON invnumS (invnum_N);    
        """ % num);
    print "  -", "Generated invnumS", datetime.datetime.now()

    c.executescript("""
        DROP TABLE IF EXISTS invnumM;
        CREATE TEMPORARY TABLE invnumM AS
                SELECT  min(invnum) AS invnum, invnum_N
              FROM  invnumS
          GROUP BY  invnum_N;
        CREATE INDEX invnum2  ON invnumM (invnum);
        CREATE INDEX invnumN2 ON invnumM (invnum_N);    
        """)
    print "  -", "Generated invnumM", datetime.datetime.now()

    updR = c.execute("""
        SELECT  b.invnum_N, a.invnum_N
          FROM  invnumM AS a
    INNER JOIN  invnumS AS b
            ON  a.invnum_N=b.invnum
         WHERE  b.invnum_N!=a.invnum_N
        """).fetchall()
    print "  -", "Inner join", datetime.datetime.now()
    print updR[:4], len(updR)

    if len(updR)>0:
        c.executemany("UPDATE invpat_%d_sort SET invnum_N = ? WHERE invnum_N = ?" % num, updR)
        print "  -", "Initial update", datetime.datetime.now()
        updR = c.execute("""
            SELECT  min(invnum) as invnum, invnum_N
              FROM  invpat_%d_sort
          GROUP BY  invnum_N
            """ % num).fetchall()
        c.executemany("UPDATE invpat_%d_sort SET invnum_N = ? WHERE invnum_N = ?" % num, updR)
        print "  -", "Final update", datetime.datetime.now()
