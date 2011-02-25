from igraphSen import *
from senAdd import *
import copy, csv, datetime, sqlite3, types, random

def def_plot(g, layout="fr", vs_nm=None):
    if vs_nm==None:
        plot(g, layout=g.layout(layout))
    else:
        plot(g, layout=g.layout(layout), vertex_label=[str(x) for x in g.vs[vs_nm]])

class senGraph:
    def __init__(self, lst, varType="edge", vs_nm="inventor_id", sort=True, debug=False):
        if str(type(lst))=="<class 'igraph.Graph'>":
            self.g = lst
        elif str(type(lst))=="<class 'igraphSen.GraphSen'>":
            self.g = lst
        else:
            tab = False
            if str(type(lst))=="<type 'instance'>":
                tab = True
            
            if varType=="vertex" and tab:
                import types
                t = lst
                self.g = GraphSen()
                self.g.add_vertices(len(lst.vList)-1)
                try:
                    vList = zip(*lst.vList)
                    self.g.vs[vs_nm] = vList[0]
                    for i, fld in enumerate(lst.vlst):
                        self.g.vs[str(fld)] = vList[1+i]
                except:
                    self.g.vs[vs_nm] = lst.vList
                vDct = dict([[x, i] for i,x in enumerate(self.g.vs[vs_nm])])
                self.g.add_edges(map(lambda x: [vDct[x[0]], vDct[x[1]]], lst.eList))

                if len(lst.eList)>0 and len(lst.eList[0])>2:
                    eList = zip(*lst.eList)
                    for i, fld in enumerate(lst.elst):
                        self.g.es[str(fld)] = eList[2+i]
                
            elif varType=="edge":
                count = 0
                gDict = {}
                gList = []
                if tab:
                    tabL = copy.copy(lst)
                    lst = tabL.eList
                    
                #edge approach
                for x in lst:
                    rList = []
                    for y in x[:2]: #just grab the first two
                        if y not in gDict:
                            gDict[y]=count
                            count = count + 1
                        rList.append(gDict[y])
                    gList.extend([rList])

                if sort:
                    node_list = [x[0] for x in sorted(gDict.items(), key=lambda x: x[1])]
                    sort_list = sorted(node_list)
                    node_list = [sort_list.index(x) for x in node_list]
                    gList = [[node_list[x[0]], node_list[x[1]]] for x in gList]
                self.g = GraphSen(gList)

                if sort:
                    self.g.vs[vs_nm] = sort_list
                else:
                    self.g.vs[vs_nm] = [x[0] for x in sorted(gDict.items(), key=lambda x: x[1])]

                if tab:
                    self.vs_add(tabL.vList,  tabL.vlst)
                    self.es_add(tabL.eList,  tabL.elst)
                    self.component_attrib()
                    
                if debug:
                    print gList
                    print [x[0] for x in sorted(gDict.items(), key=lambda x: x[1])]

    def vs_add(self, dset, field, vs_nm="inventor_id"):
        if type(field)==types.StringType:
            vs_dct = dict([[z[0], len(z)==2 and z[-1] or z[1:]] for z in dset])
            self.g.vs[field] = [vs_dct[x] for x in self.g.vs[vs_nm]]
        elif type(field)==types.ListType:
            for i,fld in enumerate(field):
                try:
                    vs_dct = dict([[z[0], z[1+i]] for z in dset])
                    self.g.vs[str(fld)] = [vs_dct[x] for x in self.g.vs[vs_nm]]
                except:
                    print z

    def es_add(self, dset, field):
        for i,fld in enumerate(field):
            self.g.es[str(fld)] = [x[i] for x in dset]

    def vs_cent_label(self, filt, label, number=1, size=5):
        self.g.vs["prank"] = self.g.pagerank(damping=0.95, directed=False)

        centLst = []        
        for x in set(self.g.vs[filt]):
            filter_list = sorted([self.g.vs["prank"][j] for j,y in enumerate(self.g.vs[filt]) if x==y], reverse=True)
            if len(filter_list)>=size:
                centLst.append([x, [number, (lambda j,y: j==1 and [y[0]] or y[:j])(number, filter_list)]])
        centDct = dict(centLst)

        labLst = []
        for i,x in enumerate(self.g.vs[filt]):
            labLst.append("")
            if x in centDct:
                if centDct[x][0]>0:
                    if self.g.vs["prank"][i] in centDct[x][1]:
                        centDct[x][0] = centDct[x][0] - 1
                        labLst[-1] = self.g.vs[label][i]

        self.g.vs["label"] = labLst

    def vs_color(self, field, rand=True, dbl=False):
        ln = self.g.vs[field];
        asgCnt = sorted([[x, ln.count(x)] for x in set(ln) if x!=""], reverse=True, key=lambda(x): x[1])
        if dbl:
            col = []
            for x in colors:
                for y in colors:
                    if x[1]!=y[1]:
                        col.append([x[1], y[1]])
        else:
            col = [x[1] for x in colors]
        col = rand and random.sample(col, len(col)) or col
        def hexIt():
            return hex(int(256*random.random()))[-2:].replace("x", "0")
        def colHex():
            heX = "#%s%s%s" % (hexIt(), hexIt(), hexIt())
            return [colGrad("#FFFFFF", heX, 35), heX]
        asgDct = dict([[x[0], (i<len(col)) and col[i] or colHex()] for i,x in enumerate(asgCnt)])
        if dbl:
            asgDct[""] = ["#FFFFFF", "#F0F0F0"]
            self.g.vs["color"] =  [asgDct[x][0] for x in ln]
            self.g.vs["color2"] = [asgDct[x][1] for x in ln]
        else:
            asgDct[""] = "#F8F8F8"
            self.g.vs["color"] = [x=="" and "#F8F8F8" or asgDct[x] for x in ln]

    def es_sel(self, varN, ge=None, le=None, eq=None):
        if ge!=None and le!=None:
            exec("sub = self.g.es(%s_ge=%s, %s_le=%s);" % (varN, ge, varN, le))
        elif ge!=None:
            exec("sub = self.g.es(%s_ge=%s);" % (varN, ge))
        elif le!=None:
            exec("sub = self.g.es(%s_le=%s);" % (varN, le))
        elif eq!=None:
            exec("sub = self.g.es(%s_eq=%s);" % (varN, eq))
                 
        z = [x.tuple[0] for x in sub]
        z.extend([x.tuple[1] for x in sub])
        g = self.g.subgraph(list(set(z)))

        if ge!=None:
            exec("g.delete_edges(%s_lt=%s);" % (varN, ge))
        if le!=None:
            exec("g.delete_edges(%s_gt=%s);" % (varN, le))        
        if eq!=None:
            exec("g.delete_edges(%s_ne=%s);" % (varN, eq))
        return g

    def __repr__(self):
        return "%s" % summary(self.g)

    def component(self, num=1, debug=False):
        mem = self.g.clusters().membership
        if debug:
            print "Members: %s" % (max(mem)+1)
            
        if num<1:
            num=1
        elif num>max(mem)+1:
            num = max(mem)+1
        com = [[mem.count(x), x] for x in range(0, max(mem)+1)]
        com.sort(reverse=True)
        if debug:
            print [x[0] for x in com[num-1: min(len(com), num+4)]]
        return self.g.clusters().subgraph(com[num-1][1])            

    def component_attrib(self, var_name="component"):
        mem = self.g.clusters().membership
        com = [[mem.count(x), x] for x in range(0, max(mem)+1)]
        com.sort(reverse=True)
        com = [[x[1], i] for i,x in enumerate(com)]
        com.sort()
        self.g.vs[var_name] = [com[x][1] for x in mem]

    def neighborhood(self, vx, order=1):
        listed = []
        for i in range(0, order):
            for num in vx:
                listed.extend([num])
                listed.extend(self.g.neighbors(num))
                vx = list(set(listed))
        return senGraph(self.g.subgraph(vx))

    def __KML_rng(self, lst, scale):
        return min(lst), scale/(max(lst)==min(lst) and 0.1 or max(lst)-min(lst))
    def __KML_eDt(self, edgeDict, x):
        if x[0] in edgeDict:
            if x[1] not in edgeDict[x[0]]:
                edgeDict[x[0]].append(x[1])
        else:
            edgeDict[x[0]] = [x[1]]
        return edgeDict

    def json(self, output='d.json', layout="layout", title='Visual', scale=[25., 15.],
             vBool=['NIH', 'NSF'], block=[['AsgNum', 'Assignee']]):
        if not(layout in self.g.vs.attribute_names()):
            self.g.vs[layout] = self.g.layout("FR")
        import json
        self.g.vertex_attributes()
        if scale!=None:
            xSc = self.__KML_rng([x[0] for x in self.g.vs[layout]], scale[0])
            ySc = self.__KML_rng([x[1] for x in self.g.vs[layout]], scale[1])
        else:
            xSc = [0, 1]
            ySc = [0, 1]

        edgeDict = {}
        for x in self.g.get_edgelist():
            edgeDict = self.__KML_eDt(edgeDict, list(x))
            edgeDict = self.__KML_eDt(edgeDict, list(reversed(x)))

        def cap(string):
            try:
                return " ".join(["%s%s" % (x[0], x[1:].lower()) for x in string.split(" ")])
            except:
                return ""
        def name(vs):
            return "%s, %s" % (cap(vs["Lastname"][0]), cap(vs["Firstname"][0]))

        order = sorted([[name(self.g.vs(i)), i] for i,x in enumerate(self.g.vs)])
        order = [x[1] for x in order]
        ordDct = dict([[x, i] for i,x in enumerate(order)])

        edgeDict = dict([[k, {'edge':sorted([ordDct[y] for y in x])}]
                          for k,x in edgeDict.iteritems()])

        blockDct = [{} for x in block]
        for k,y in enumerate(block):
            for i,x in enumerate(self.g.vs()):
                blockDct[k][x[y[0]]] = x[y[1]]
            blockDct[k] = dict([[x[0], [i, x[1]]] for i,x in enumerate(blockDct[k].items())])

        #--------------

        marks = [{'pos': self.g.vs[layout][i],
                  'col':[self.g.vs["color"][i][1:], self.g.vs["color2"][i][1:]],
                  'size':self.g.vs["size"][i],
                  'name':name(self.g.vs(i)),
                  'asg':cap(self.g.vs["Assignee"][i]),
                  'edge':i in edgeDict and edgeDict[i]['edge'] or [],
                  'vBool':dict([[x, self.g.vs[x][i]!="" and 1 or 0] for x in vBool]),
                  'block':dict([[x[0], blockDct[k][self.g.vs[x[0]][i]][0]] for k,x in enumerate(block)]),
                  'AsgNum':self.g.vs["AsgNum"][i]
                 }
                 for i in order]
        json = json.dumps({'block':dict([[x[1], [cap(y) for j,y in sorted(blockDct[k].values())]] for i,x in enumerate(block)]),
                           'marks': marks, 'sc':[xSc, ySc], 'title':title}, separators=(',',':'))

        #--------------

        if output==None:
            return json
        else:
            f = open(output, 'wb')
            f.write("var data = ")
            f.write(json)
            f.close()
    
    def KML(self, output=None, color="color", layout="layout",
            defColor="#63B8FF", scale=[25., 15.], edgeDraw=True):
        KMLstr = ""

        if not(layout in self.g.vs.attribute_names()):
            self.g.vs[layout] = self.g.layout("KK")
        
        KMLstr = """%s
                <Style id="line"><LineStyle>
                    <color>#88aaaaaa</color>
                    <width>1</width>
                </LineStyle></Style>""" % (KMLstr)

        #Determine ranges
        if scale!=None:
            xSc = self.__KML_rng([x[0] for x in self.g.vs[layout]], scale[0])
            ySc = self.__KML_rng([x[1] for x in self.g.vs[layout]], scale[1])
        else:
            xSc = [0, 1]
            ySc = [0, 1]

        if edgeDraw:
            edgeDict = {}
            for x in self.g.get_edgelist():
                edgeDict = self.__KML_eDt(edgeDict, list(x))
                edgeDict = self.__KML_eDt(edgeDict, list(reversed(x)))

            for k,x in edgeDict.iteritems():
                linestr = ""
                for y in x:
                    linestr = "%s%f,%f %f,%f " % (linestr, 
                       xSc[1]*(self.g.vs["layout"][k][0]-xSc[0]),
                       ySc[1]*(self.g.vs["layout"][k][1]-ySc[0]),
                       xSc[1]*(self.g.vs["layout"][y][0]-xSc[0]),
                       ySc[1]*(self.g.vs["layout"][y][1]-ySc[0]))
                KMLstr = """%s
                    <Placemark>
                        <styleUrl>#line</styleUrl>
                        <LineString>
                            <coordinates>%s</coordinates>
                        </LineString>
                    </Placemark>"""  % (KMLstr, linestr.strip())

        for i,x in enumerate(self.g.vs):
            col = color in self.g.vs.attribute_names() and x[color][1:] or defColor[1:]
            KMLstr = """%s
                <Placemark>
                    <name>#%d</name>
                    <description>%s</description>
                    <Style>
                        <IconStyle>
                            <Icon>
                                <href>http://140.247.116.250/mptest.py/image2?c0=%s&amp;r=%d</href>
                            </Icon>
                        </IconStyle>
                    </Style>
                    <Point><coordinates>%f,%f</coordinates></Point>
                </Placemark>""" % (KMLstr,
                                   i, x["name"], col, x["size"],
                                   xSc[1]*(x["layout"][0]-xSc[0]),
                                   ySc[1]*(x["layout"][1]-ySc[0]))
        return """
            <?xml version="1.0" encoding="UTF-8"?>
            <kml xmlns="http://www.opengis.net/kml/2.2"> 
                <Document>
                    <name>%s</name>
                    <description>%s</description>
                    %s
                </Document>
            </kml>""" % ("", "", KMLstr)

#THIS ALLOWS US TO INTERFACE WITH OUR DATABASES.  Not super generalizable now, but will be in the future
##class senDB:
##    def __init__(self, table=None, bbox=None, db="sqlite", fname=None, dbconfig={}, eCnt=250, database=None):
##        #delete from vertex where lat is null or lng is null or state in ('GU', 'HI', 'AK', 'PR', 'VI');
##        #create table e_state as select h, t, count(*) as cnt from (select a.State as h, b.State as t from vertex as a inner join vertex as b where a.state < b.state and a.Patent=b.Patent) as tbl group by h,t;
##        #create table v_state as select state, lat, lng, count(*) as cnt from vertex group by state
##
##        self.db_type = db;
##        
##        if db=="MySQL":
##            import MySQLdb
##            conn = MySQLdb.connect(passwd=dbconfig["passwd"], db=dbconfig["db"], host=dbconfig["host"], user=dbconfig["user"])
##            c = conn.cursor()
##            if bbox==None:
##                c.execute("SELECT * FROM v_%s" % table)
##            else:
##                c.execute("SELECT %s, lat, lng, count(*) as cnt FROM %s GROUP BY %s" %
##                    (table[0], "vertex WHERE lat>%f AND lng>%f AND lat<%f AND lng<%f" % tuple(bbox), table[0]))
##            self.vList = c.fetchall()
##            self.vlst = [x[0] for x in c.description] #column names
##            self.vlst.pop(0)
##            if bbox==None:
##                c.execute("SELECT * FROM e_%s LIMIT %d" % (table, eCnt))
##            else:
##                c.execute("SELECT h%s AS h, t%s AS t, count(*) as cnt FROM edge WHERE %s AND %s GROUP BY h%s, t%s" % \
##                      (table[1], table[1],
##                       "tLat>%f AND tLng>%f AND tLat<%f AND tLng<%f" % tuple(bbox),
##                       "hLat>%f AND hLng>%f AND hLat<%f AND hLng<%f" % tuple(bbox),
##                       table[1], table[1]))
##                
##            self.eList = c.fetchall()
##            self.elst = [x[0] for x in c.description]
##            self.elst.pop(0)
##            c.close()
##            conn.close()

class senDBMySQL:
    def __init__(self, dbconfig, table="invpat"):
        """
            dbconfig should be (h)ost, (u)ser, (p)asswd, (d)b
        """
        self.table = table
        self.dbconfig = dbconfig
        self.open()

    def open(self):
        import MySQLdb
        self.conn = MySQLdb.connect(passwd=self.dbconfig["p"], db=self.dbconfig["d"], host=self.dbconfig["h"], user=self.dbconfig["u"])
        self.c = self.conn.cursor()

    def close(self):
        self.close()
        self.conn.close()

    def graph(self, vertex_list=None, where=None, flag=[], output=":memory:"):
        import datetime, SQLite, os

        oldfile = os.path.isfile(output) and True or False
        s = SQLite.SQLite(output, tbl="G0")
        if not(oldfile):
            if vertex_list != None:
                if type(vertex_list) in (types.ListType, types.TupleType):
                    vx = [(x[0],) for x in vertex_list]
                else:
                    vx = [(x,) for x in vertex_list]

                self.c.execute("CREATE TEMPORARY TABLE gmerge (Invnum_N VARCHAR(255), Unique(Invnum_N));")
                self.c.executemany("INSERT IGNORE INTO gmerge VALUES (%s)", vx)
                self.c.execute("""            
                    CREATE TEMPORARY TABLE G0 AS
                        SELECT  a.*
                          FROM  %s AS a
                    INNER JOIN  gmerge AS b
                            ON  a.Invnum_N=b.Invnum_N
                            %s;
                    """ % (self.table, (where!=None) and "WHERE %s" % where or ""))
                #flag gets created here...
            elif where==None:
                self.c.execute("""
                    CREATE TEMPORARY TABLE G0 AS
                        SELECT  a.*
                          FROM  %s AS a
                    INNER JOIN  gmerge AS b
                            ON  a.Invnum_N=b.Invnum_N
                         WHERE  %s;""" % self.table, where)

            # CREATE SQLite Data
            self.c.execute("DESCRIBE invpat")
            s.conn.create_function("flag", 1, lambda x:x in flag and "x" or "")
            s.c.execute("CREATE TABLE G0 (%s)" % ", ".join([" ".join(x[:2]) for x in self.c.fetchall()]))
            self.c.execute("SELECT * FROM G0")
            s.addSQL(data=self.c.fetchall())
            s.add("flag", "")
            s.c.execute("UPDATE G0 SET flag=flag(Invnum_N);")

            #how do we incorporate new fields?
            s.c.executescript("""
                DROP TABLE IF EXISTS vx0;
                DROP TABLE IF EXISTS ed0;
                CREATE INDEX IF NOT EXISTS G0_AY ON G0 (AppYear);
                CREATE INDEX IF NOT EXISTS G_id ON G0 (Patent);
                CREATE INDEX IF NOT EXISTS G_ed ON G0 (Invnum_N, Patent);
                CREATE TABLE vx0 AS
                    SELECT  Invnum_N AS id, count(*) AS cnt, *,
                            GROUP_CONCAT(Class) AS Classes
                      FROM  G0
                  GROUP BY  Invnum_N
                  ORDER BY  AppYear;
                CREATE INDEX IF NOT EXISTS vx_id ON vx0 (Invnum_N);
                CREATE TABLE ed0 AS
                    SELECT  a.Invnum_N AS h, b.Invnum_N AS t, a.AppYear AS AppYear, a.Patent AS Patent, a.Class AS Class
                      FROM  G0 AS a INNER JOIN G0 AS b
                        ON  a.Patent=b.Patent AND a.Invnum_N<b.Invnum_N;
                """)
            
        self.tab = senTab()
        self.tab.vList = s.c.execute("SELECT * FROM vx0").fetchall()
        self.tab.vlst  = s.columns(table="vx0", output=False)[1:]
        self.tab.eList = s.c.execute("SELECT * FROM ed0").fetchall()
        self.tab.elst  = s.columns(table="ed0" , output=False)[2:]
        s.close()

    def congdist(self, cd, state):
        self.c.execute("SELECT Invnum_N FROM invpat WHERE cd=%s AND state=%s", (cd, state))
        return self.c.fetchall()

    def nhood(self, InvList, loop=2):
        if type(InvList[0]) in (types.ListType, types.TupleType):
            InvList = [(x[0],) for x in InvList]
        else:
            InvList = [(x,) for x in InvList]
        #self.c.execute("DROP TABLE IF EXISTS omerge;")
        self.c.execute("CREATE TEMPORARY TABLE omerge (Invnum_N VARCHAR(255), Unique(Invnum_N));")
        self.c.execute("CREATE INDEX mI ON omerge (Invnum_N);")
        #self.c.execute("DROP TABLE IF EXISTS pmerge;")
        self.c.execute("CREATE TEMPORARY TABLE pmerge (Patent VARCHAR(255), Unique(Patent));")
        self.c.execute("CREATE INDEX m2 ON pmerge (Patent);")
        for i in range(0, loop):
            self.c.executemany("INSERT IGNORE INTO omerge VALUES (%s)", InvList)
            self.c.execute("""
                INSERT IGNORE INTO pmerge
                    SELECT  b.Patent
                      FROM  omerge AS a
                INNER JOIN  invpat AS b
                        ON  a.Invnum_N = b.Invnum_N;
                """)
            self.c.execute("""
                INSERT IGNORE INTO omerge
                    SELECT  b.Invnum_N
                      FROM  pmerge AS a
                INNER JOIN  invpat AS b
                        ON  a.Patent = b.Patent;
                """)
            self.c.execute("SELECT * FROM omerge")
            InvList = self.c.fetchall()
        return InvList        
        

















class senDBSQL:
    def __init__(self, db=None, table=None):
        import SQLite
        self.table = (table==None and "invpat" or table)
        self.sql = SQLite.SQLite(db=(db==None and "/home/ron/disambig/sqlite/invpat.sqlite3" or db), tbl=self.table)
        self.sql.open()

    def graph(self, vertex_list=None, where=None, flag=[]):
        if vertex_list != None:
            if type(vertex_list) in (types.ListType, types.TupleType):
                vx = [((type(x) in (types.ListType, types.TupleType) and x[0] or x),) for x in vertex_list]
            else:
                vx = [(x,) for x in vertex_list]

            self.sql.conn.create_function("flag", 1, lambda x:x in flag and "x" or "")
            self.sql.c.executescript("""
                DROP TABLE IF EXISTS omerge;
                CREATE TEMPORARY TABLE omerge (Invnum_N VARCHAR(255), Unique(Invnum_N));
                CREATE INDEX mI ON omerge (Invnum_N);
                """)
            self.sql.c.executemany("INSERT OR IGNORE INTO omerge VALUES (?)", vx)
            self.sql.c.executescript("""
                DROP TABLE IF EXISTS G0;
                CREATE TEMP TABLE G0 AS
                    SELECT  a.*, flag(a.Invnum_N) AS flag
                      FROM  %s AS a
                INNER JOIN  omerge AS b
                        ON  a.Invnum_N=b.Invnum_N;
                """ % self.table)

        elif where==None:
            self.sql.c.executescript("""
                DROP TABLE IF EXISTS G0;
                CREATE TEMP TABLE G0 AS
                    SELECT * FROM %s WHERE %s;
                """ % self.table, where)

        #how do we incorporate new fields?
        self.sql.c.executescript("""
            DROP TABLE IF EXISTS vx0;
            DROP TABLE IF EXISTS ed0;
            CREATE INDEX IF NOT EXISTS G0_AY ON G0 (AppYear);
            CREATE INDEX IF NOT EXISTS G_id ON G0 (Patent);
            CREATE INDEX IF NOT EXISTS G_ed ON G0 (Invnum_N, Patent);
            CREATE TEMPORARY TABLE vx0 AS
                SELECT  Invnum_N AS id, count(*) AS cnt, *,
                        GROUP_CONCAT(Class) AS Classes
                  FROM  G0
              GROUP BY  Invnum_N
              ORDER BY  AppYear;
            CREATE INDEX IF NOT EXISTS vx_id ON vx0 (Invnum_N);
            CREATE TEMPORARY TABLE ed0 AS
                SELECT  a.Invnum_N AS h, b.Invnum_N AS t, a.AppYear AS AppYear, a.Patent AS Patent, a.Class AS Class
                  FROM  G0 AS a INNER JOIN G0 AS b
                    ON  a.Patent=b.Patent AND a.Invnum_N<b.Invnum_N;
            """)
            
        self.tab = senTab()
        self.tab.vList = self.sql.c.execute("SELECT * FROM vx0").fetchall()
        self.tab.vlst  = self.sql.columns(table="vx0", output=False)[1:]
        self.tab.eList = self.sql.c.execute("SELECT * FROM ed0").fetchall()
        self.tab.elst  = self.sql.columns(table="ed0" , output=False)[2:]

        #columns and values
        self.tab.allData = [self.sql.columns(table="G0" , output=False)]
        self.tab.allData.extend(self.sql.c.execute("SELECT * FROM G0").fetchall())

    def nhood(self, InvList, loop=2):
        if type(InvList[0]) in (types.ListType, types.TupleType):
            InvList = [(x[0],) for x in InvList]
        else:
            InvList = [(x,) for x in InvList]
        self.sql.c.executescript("""
            DROP TABLE IF EXISTS omerge;
            CREATE TEMPORARY TABLE omerge (Invnum_N VARCHAR(255), Unique(Invnum_N));
            CREATE INDEX mI ON omerge (Invnum_N);
            
            DROP TABLE IF EXISTS pmerge;
            CREATE TEMPORARY TABLE pmerge (Patent VARCHAR(255), Unique(Patent));
            CREATE INDEX m2 ON pmerge (Patent);            
            """)
        for i in range(0, loop):
            self.sql.c.executemany("INSERT OR IGNORE INTO omerge VALUES (?)", InvList)
            self.sql.c.executescript("""
                INSERT OR IGNORE INTO pmerge
                    SELECT  b.Patent
                      FROM  omerge AS a
                INNER JOIN  invpat AS b
                        ON  a.Invnum_N = b.Invnum_N;
                INSERT OR IGNORE INTO omerge
                    SELECT  b.Invnum_N
                      FROM  pmerge AS a
                INNER JOIN  invpat AS b
                        ON  a.Patent = b.Patent;
                """)
            InvList = self.sql.c.execute("SELECT * FROM omerge").fetchall()
        return InvList        

class senTab:
    def __init__(self, csv_file=""):
        ##print "Note: First row in CSV must contain filed names"
        self.recs = 0
        self.files = 0
        self.sTab = {}
        if csv_file!="":
            self.addCsv(csv_file)

    def addCsv(self, csv_file):
        senv = csv.reader(open(csv_file))
        senv = [x for x in senv]
        headers = senv[0]
        for i,x in enumerate(senv[0]):
            if x not in self.sTab:
                self.sTab[x] = ["" for y in range(0, self.recs)]
            self.sTab[x].extend([y[i] for y in senv[1:]])
        self.recs = self.recs + len(senv) - 1

    #the basic disambiguation, name ONLY
    def au_dis1(self, tag="AU"):
        damg = sorted([[x.upper(),i] for i,x in enumerate(self.sTab[tag])])
        order = [x[1] for x in damg]
        dlist = [[x[0]] for x in damg]
        inum = 0
        dlist[0].append(0)
        for i in range(1, len(dlist)):
            if dlist[i][0]!=dlist[i-1][0]:
                inum = inum + 1
            dlist[i].append(inum)
        self.sTab["InvID"] = [x[1] for x in sorted([[order[i], dlist[i][-1]] for i in range(0, len(dlist))])]

    #more advanced disambiguation, implementing FUZZY
    def au_dis2(self, tag="AU", jaro=0.95):
        conn = sqlite3.connect(":memory:")
        conn.create_function("jarow",    2, invComp)
        conn.create_function("invXMtch", 1, invXMtch)
        conn.create_aggregate("uQvals",  1, uQvals)
        damg = [[x[0], x[0][:3], x[1], i] for i,x in enumerate(sorted([[x.upper(),i] for i,x in enumerate(self.sTab[tag])]))]

        c = conn.cursor()
        quickSQL(c, damg, "author0")
        c.executescript("""
            CREATE TABLE author1 AS 
                SELECT v0, v1, v2, min(v3) as v3 FROM author0 GROUP BY v0;
            CREATE INDEX au_  ON author1 (v1);
            CREATE TABLE author2 AS
                SELECT  a.v0 AS h, b.v0 AS t, a.v3 AS numH, b.v3 AS numT, jarow(a.v0, b.v0) AS jaro
                  FROM  author1 AS a
            INNER JOIN  author1 AS b
                    ON  a.v1=b.v1 and a.v3<b.v3
                 WHERE  jaro>%s;
            CREATE TABLE author3 (numT INTEGER, numH INTEGER, t VARCHAR, h VARCHAR, UNIQUE(numT));
            INSERT OR REPLACE INTO author3 
                SELECT  numT, min(numH) as numH, t, h
                  FROM  author2
              GROUP BY  numT;
            """ % str(jaro))

        while 1==1:
            c.executescript("""
                DROP TABLE IF EXISTS author4;
                CREATE TABLE author4 AS
                    SELECT  a.numT, b.numH, a.t, a.h
                      FROM  author3 AS a
                INNER JOIN  author3 AS b
                        ON  b.numT = a.numH;
                INSERT OR REPLACE INTO author3
                    SELECT * FROM author4;
                """)
            #keep self merging until no more to self merge
            if c.execute("SELECT count(*) FROM author4").fetchone()[0]==0:
                break;

        #**this removes inventors that have clear mismatches
        #EX. THOMAS, DW | THOMAS, D	| THOMAS, DY
        #    Matches per THOMAS, D but DW <> DY
        c.executemany("DELETE FROM author3 WHERE numH=?",
                      c.execute("""
                            SELECT  numH
                              FROM  author3
                          GROUP BY  numH
                            HAVING  invXMtch(uQvals(t))
                            """).fetchall())

        #final "disambiguated"
        c.executescript("""
            CREATE TABLE author5 (inv VARCHAR, ord INTEGER, invID INTEGER, UNIQUE(ord));
            INSERT OR REPLACE INTO author5
                SELECT  a.v0, a.v2, b.v3
                  FROM  author0 AS a
            INNER JOIN  author1 AS b
                    ON  a.v0 = b.v0;
            INSERT OR REPLACE INTO author5
                SELECT  a.inv, a.ord, b.numH
                  FROM  author5 AS a
            INNER JOIN  author3 AS b
                    ON  a.invID = b.numT;
            """)

        self.sTab["InvID"] = [x[0] for x in c.execute("SELECT invID FROM author5 ORDER BY ord")]
        c = None
        conn = None

    def csv_graph(self, vertex="InvID", edge="UT", vertex_lst=["AU"], vertex_agg=[], edge_lst=["TI", "JI", "PD", "PY", "SC", "TC"], output="wosc", index=True):
        t = datetime.datetime.now()
        print output

        if vertex not in self.sTab:
            self.au_dis2()
            print "  - disambg (%s)" % str(datetime.datetime.now()-t)

        allF = [vertex]
        allF.extend(vertex_lst)
        allF.extend([edge])
        allF.extend(edge_lst)

        conn = sqlite3.connect(":memory:")
        conn.create_aggregate("uQvals", 1, uQvals)
        c = conn.cursor()
        c.execute("CREATE TABLE AllData (%s, %s, %s, %s);" % 
                  ("%s INTEGER" % vertex, "%s VARCHAR" % " VARCHAR, ".join(vertex_lst),
                   "%s VARCHAR" % edge,   "%s VARCHAR" % " VARCHAR, ".join(edge_lst)));

        c.executemany("INSERT INTO AllData VALUES (%s)" % ", ".join(["?"]*(len(edge_lst)+len(vertex_lst)+1+1)),
                [[self.sTab[x][i] for x in allF] for i in range(0, self.recs)])


        if index:
            c.executescript("""
                  CREATE INDEX IF NOT EXISTS ADve   ON AllData (%s, %s);
                  CREATE INDEX IF NOT EXISTS ADvert ON AllData (%s);
                  CREATE INDEX IF NOT EXISTS ADedge ON AllData (%s);
                  """ % (vertex, edge, vertex, edge))
            print "  - Indices (%s)" % str(datetime.datetime.now()-t)

        c.executescript("""
            CREATE TABLE vertex AS 
                SELECT  %s, %s, count(*) as cnt, uQvals(%s)
                  FROM  AllData
              GROUP BY  %s;
            """ % (vertex, len(vertex_agg)==0 and ",".join(vertex_lst) or ",".join(vertex_lst[:-len(vertex_agg)])+","+",".join(vertex_agg), vertex_lst[0], vertex))
        self.csv_output(c, "vertex", output)
        print "  - vertex  (%s)" % str(datetime.datetime.now()-t)

        c.execute("""
            CREATE TABLE edge AS 
                SELECT  a.%s AS hID, b.%s AS tID, %s, %s, a.%s
                  FROM  AllData AS a
            INNER JOIN  AllData AS b
                    ON  a.%s < b.%s and a.%s = b.%s;
            """ % (vertex, vertex,
                    "a.%s" % ", a.".join(edge_lst),
                    "b.%s" % ", b.".join(edge_lst),
                   edge, vertex, vertex, edge, edge))
        self.csv_output(c, "edge", output)
        print "  - edge    (%s)" % str(datetime.datetime.now()-t)

        self.csv_output(c, "alldata", output)
        print "  - Alldata (%s)" % str(datetime.datetime.now()-t)

        self.vList = [list(x) for x in c.execute("SELECT %s, %s, cnt FROM vertex" % (vertex, ",".join(vertex_lst)))]
        self.eList = [list(x) for x in c.execute("SELECT * FROM edge")]
        #self.eListF = [list(x) for x in c.execute("SELECT * FROM edge")]

        c = None
        conn = None

        self.vlst = vertex_lst
        self.vlst.extend(["cnt"])
        self.elst = ["numT", "numH"]
        self.elst.extend(edge_lst)
        self.elst.extend([edge])

    def csv_output(self, c, table, output):
        writer = csv.writer(open("%s_%s.csv" % (output, table), "wb"), lineterminator="\n")
        writer.writerows([[x[1] for x in c.execute("PRAGMA TABLE_INFO(%s)" % table)]])
        writer.writerows(c.execute("SELECT * FROM %s" % table).fetchall())
        writer = None
        
    def __repr__(self):
        return "Recs: %d\nsTab Keys: (%d) %s" % (self.recs, len(self.sTab.keys()), str(self.sTab.keys()))

##r = senTab("websciences\wosc period 1.csv")
##r.csv_graph(output="wosc1")
##s = senGraph(r.eList)
##plot(s.component(2), layout="FR", vertex_label="")
##
##r = senTab("websciences\wosc pat 1.csv")
##r.csv_graph(vertex="invnum_N", vertex_lst=["name"],
##            edge="patent", edge_lst=["loc", "assignee", "Description"],
##            output="wscp1")
##s = senGraph(r.eList)
##plot(s.g, layout="FR", vertex_label="")
