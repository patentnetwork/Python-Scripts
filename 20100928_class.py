#unique subclass-combiation counter

import sys, datetime
sys.path.append("/home/ron/PythonBase")

import SQLite
import senAdd

s = SQLite.SQLite(db='../sqlite/class_count.sqlite3', tbl='class');
s.conn.create_function("pType", 1, senAdd.patType)
s.attach('../sqlite/class.sqlite3', name='cls')
s.replicate(table='class', db='cls')
s.add('pat_type', 'varchar(1)', table='class')
s.add('fullcls', 'text', table='class')
s.index(keys=['Patent', 'FullCls'], table="class", unique=True)
s.index(keys=['Pat_Type'], table="class", unique=False)
s.count()
s.c.execute("INSERT OR IGNORE INTO class SELECT *, pType(patent), class||'-'||subclass FROM cls.class")
s.commit()
s.count()
#I don't want to really deal with non utility patents right now, delete them
s.c.execute("DELETE FROM class WHERE pat_type!='U'")
s.commit()
s.count()
#First CLASS-SUBCLASS combinations, elimanate these
cls = s.c.execute("SELECT min(Patent), FullCls FROM class GROUP BY FullCls").fetchall()
s.c.executemany("DELETE FROM class WHERE patent=? and FullCls=?", cls)
s.commit()
s.count()
#Determine all possible pairs for each patent
s.c.execute("""
    CREATE TABLE class_pair AS
        SELECT  a.patent AS patent, 
                a.FullCls AS clsA,
                b.FullCls AS clsB
          FROM  class AS a
    INNER JOIN  class AS b
            ON  a.patent=b.patent AND a.FullCls<b.FullCls;
    """)
s.index(keys=['clsA', 'clsB'], table="class_pair")
s.count(table="class_pair")
#Determine number of patents and associated counts
s.c.execute("""
    CREATE TABLE class_paircnt AS
        SELECT  Patent,count(*) as cnt FROM
           (SELECT  min(Patent) AS Patent
              FROM  class_pair
          GROUP BY  clsA, clsB)
        GROUP BY Patent;
      """)
s.index(keys=['Patent'], table="class_paircnt")
s.count(table="class_paircnt")
    




s.close()
