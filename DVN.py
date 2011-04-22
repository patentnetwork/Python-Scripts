import sqlite3, sys, SQLite, igraph, csv, senGraph, datetime

# TODO:
# Calculate component ranking and assign a component identifier
# Calculate eigenvector centrality within components
# Add function to get vertices of the component number

# Option 1: run the script directly from the command line
# TODO: implement this!

def time_printer(program_start = 0, calc_start = 0):
    now = datetime.datetime.now()
    if(program_start):
        print "Time elapsed: ", now - program_start
    if(calc_start):
        print "Calculation time: ", now - calc_start

def DVN_script(filepath = "/home/ayu/DVN/", dbnames = []):
    """
    script to create and run DVN object from command line

    To run:
    python DVN.py <directory> <database names - variable length, separate by spaces>

    Example:
    python DVN.py /home/ayu/DVN/ invpat
    
    (1) Create network data files based on invpat for upload to DVN (graphml format)
    (2) Create csv files for data and pre-calculated network measures
        network measures calculated:
            node measures:
                - centrality (degree, betweenness)
                - clustering coefficient
                - constraint
                - component number
            edge measures:
                - betweenness
    
    """
    t1 = datetime.datetime.now()
    print "Start", t1   
    print filepath
    print dbnames
    D = DVN(filepath, dbnames)
    D.create_graphs()
##    print "calculating node betweenness.."
##    D.calculate_node_betweenness()
##    print "calculating pagerank..."
##    D.calculate_PageRank()
##    print "calculating edge betweenness..."
##    D.calculate_edge_betweenness()
    time_printer(t1)
    t2 = datetime.datetime.now()
    print "calculating constraint..."
    D.calculate_constraint()
    time_printer(t1, t2)
    t2 = datetime.datetime.now()
    print "calculating transitivity..."
    D.calculate_clustering_coefficient()
    time_printer(t1, t2)
    t2 = datetime.datetime.now()
    print "calculating degree..."
    D.calculate_degree()
    time_printer(t1, t2)
    t2 = datetime.datetime.now()
    print "calculating component ranking..."
    D.calculate_component()
    time_printer(t1, t2)
    t2 = datetime.datetime.now()
    print "calculating eigenvector centrality..."
    D.calculate_eigenvector_centrality()
    time_printer(t1, t2)
    t2 = datetime.datetime.now()
##    print "calculating subclasses..."
##    D.calculate_subclasses()
##    time_printer(t1, t2)
##    t2 = datetime.datetime.now()
##    print "calculating citation counts..."
##    D.calculate_citations()
##    time_printer(t1, t2)
##    t2 = datetime.datetime.now()
##    print "calculating total inventors per patent..."
##    D.calculate_inventor_count()
##    time_printer(t1, t2)
##    t2 = datetime.datetime.now()
    D.summary()
    print "creating graphml network files for 2000-2003"
    D.create_graphml_file()
    time_printer(t1, t2)
    t2 = datetime.datetime.now()
    print "creating csv files for 1975-2010"
    D.create_csv_file()
    time_printer(t1, t2)
    print "DONE"
    time_printer(t1)
    

# Option 2: run interactively in Python
# create a DVN object, various functions available within to use and reuse

class DVN():
    """
    initialize a DVN object for uploading patent data to the IQSS DVN
    """

    def __init__(self, filepath, dbnames, graphml = '', begin = 1975, end = 2010, increment = 3):
        """
        takes a filepath string and a list of dbnames
        if graphml files already exist, take the list of files and read into graph list as graph objects

        ex:
        import DVN
        D = DVN.DVN(filepath='/home/ayu/DVN/', dbnames=['patent', 'invpat', 'citation', 'class'], graphml = ['pat_2000.graphml', 'pat_2003.graphml'])
        D.summary()
        D.create_csv_file()
        """
        self.filepath = filepath
        self.data = {}
        self.graphs = {}
        self.begin = begin
        self.end = end
        self.increment = increment
        for dbname in dbnames:
            self.data[dbname] = SQLite.SQLite(filepath + dbname + '.sqlite3', dbname)
        if graphml:
            i = 0
            for year in range(self.begin, self.end, self.increment):
                self.graphs[year] = igraph.Graph.Read_GraphML(filepath+graphml[i])
                i = i + 1
        

    def create_graphs(self):
        """
        create graphML files from the inventor-patent dataset
        for upload to DVN interface (by application year)

        inherits the igraph function from the patent team SQLite library
        """
        for year in range(self.begin, self.end, self.increment):
            print "Creating graph for {year}".format(year=year)
            self.graphs[year] = self.data['invpat'].igraph(where='AppYearStr BETWEEN %d AND %d' %
                                  (year, year+2), vx="invnum_N").g

    def calculate_node_betweenness(self):
        """calculate betweenness for each node in the network all networks"""
        for g in self.graphs.itervalues():
            g.vs['betweenness'] = g.betweenness()

    def calculate_eigenvector_centrality(self, year='', component=''):
        """calculate eigenvector centrality for each node all networks"""
        # calculate eigenvector centrality within each component
        if(year):
            return self.graphs[year].subgraph(self.graphs[year].vs.
                                              select(component_eq=component)).eigenvector_centrality()
        else:
            for g in self.graphs.itervalues():
                g.vs['eigenvector_centrality'] = g.eigenvector_centrality()

    def calculate_constraint(self):
        """calculate constraint for each node in all networks
        """
        for g in self.graphs.itervalues():
            g.vs['constraint'] = g.constraint()

    def calculate_clustering_coefficient(self):
        """calculate the clustering coefficient (transitivity) for each node in all networks"""
        for g in self.graphs.itervalues():
            g.vs['clustering_coefficient'] = g.transitivity_local_undirected()

    def calculate_degree(self):
        """calculate degree centrality for each node in all networks"""
        for g in self.graphs.itervalues():
            g.vs['degree'] = g.degree()

    def calculate_PageRank(self, year='', component=''):
        """calculate pagerank for each node in all networks"""
        if(year):
            return self.graphs[year].subgraph(self.graphs[year].vs.select(component_eq=component)).pagerank()
        else:
            for g in self.graphs.itervalues():
                g.vs['PageRank'] = g.pagerank()

    def calculate_edge_betweenness(self):
        """calculate edge betweennness for all edges
        """
        for g in self.graphs.itervalues():
            g.es['betweenness'] = g.edge_betweenness()

    def calculate_component(self):
        """within each graph, calculate the component that each node belongs to
        """
        for g in self.graphs.itervalues():
            print g
            mem = g.clusters().membership
            com = [[mem.count(x),x] for x in range(0,max(mem)+1)]
            com.sort(reverse=True)
            com = [[x[1], i] for i,x in enumerate(com)]
            com.sort()
            g.vs['component']=[com[x][1] for x in mem]
            #print g.vs['component']

    def calculate_subclasses(self):
        """calculate the number of subclasses per patent
        SQL:
        select patent, count(subclass) as num_subclasses from class group by patent
        """
        self.data['invpat'].add('num_subclasses', 'INT')
        self.data['class'].c.execute("select count(subclass), patent from class group by patent")
        count = self.data['class'].c.fetchall()
        print count[:10]
        self.data['invpat'].c.executemany("UPDATE invpat SET num_subclasses=? WHERE patent=?", count)
        self.data['invpat'].conn.commit()

    def calculate_citations(self):
        """calculate the number of forward and backward citations per patent
        SQL:
        select patent, count(patent) as backward_cites from citation group by patent
        select patent, count(citation) as forward_cites from citation group by patent
        """
        self.data['invpat'].add('backward_cites', 'INT')
        self.data['invpat'].add('forward_cites', 'INT')
        self.data['citation'].c.execute("select count(patent), citation from citation group by citation")
        self.data['invpat'].c.executemany("UPDATE invpat SET backward_cites=? WHERE patent=?", self.data['citation'].c.fetchall())
        self.data['invpat'].conn.commit()
        self.data['citation'].c.execute("select count(citation), patent from citation group by patent")
        self.data['invpat'].c.executemany("UPDATE invpat SET forward_cites=? WHERE patent=?", self.data['citation'].c.fetchall())
        self.data['invpat'].conn.commit()

    def calculate_inventor_count(self):
        """calculate total number of inventors per patent and add data to totalInventors column
        """
        self.data['invpat'].add('totalInventors', 'INT')
        self.data['invpat'].c.execute("select count(distinct invnum_N), patent from invpat group by patent")
        self.data['invpat'].c.executemany("UPDATE invpat SET totalInventors=? WHERE patent=?", self.data['invpat'].c.fetchall())
        self.data['invpat'].conn.commit()
        

    def get_graph(self, year):
        """returns the igraph object for the given year
        """
        return self.graphs[year]

    def get_size(self, year=2000, component=''):
        """returns the number of vertices in the given component for the given year
           if no component given, by default returns the number of vertices in the whole graph by year
        """
        if(component):
            return len(self.graphs[year].vs.select(component_eq=component))
        else:
            return len(self.graphs[year].vs)
        
    def create_graphml_file(self, year=''):
        """if year is specified, create graphml file for that specific year
        else create graphml for all years in current directory
        """
        if self.graphs.get(year):
            self.graphs[year].save((self.filepath + "pat_{year}.graphml").format(year=year))
        else:
            for k,v in self.graphs.iteritems():
                v.save((self.filepath +"pat_{year}.graphml").format(year=k))

    def summary(self):
        """print a summary of the DVN object, also prints summary network statistics per graph 
        """
        dnames = [k for k in self.data.iterkeys()]
        gnames = [k for k in self.graphs.iterkeys()]
        
        print "=========================SUMMARY========================="
        print """
                    Databases used : {dnames}
        Network graphs (by appyear): {gnames}
        """.format(dnames=dnames, gnames=gnames)
        if len(self.graphs) > 0:
            print "=========================GRAPHS=========================="
            for k,v in self.graphs.iteritems():
                print "Graph: {gname}".format(gname=str(k))
                #igraph.summary(v)
                print "Node attributes: {v}".format(v=v.vertex_attributes())
                print "Edge attributes: {e}".format(e=v.edge_attributes())
                print "---------------------------------------------------------"

    def close_data(self):
        # close all sqlite objects
        for d in self.data.itervalues():
            d.close()

    def create_csv_file(self):
        """
        create csv data file for upload to DVN interface
        step 1: slice invpat table into 3 year files
        step 2: export to csv format
        TODO: insert network data from graphs here
        """
        import unicodedata
        def asc(val):
            return [unicodedata.normalize('NFKD', unicode(x)).encode('ascii', 'ignore') for x in val]

        for year in range(self.begin, self.end, self.increment):
            #create a temporary table in memory to hold all data for each three year period
            conn = sqlite3.connect(":memory:")
            conn.executescript("""
            CREATE TABLE invpat_temp(
                Firstname TEXT,
                Lastname TEXT,
                Street TEXT,
                City TEXT,
                State TEXT,
                Country TEXT,
                Zipcode TEXT,
                Lat REAL,
                Lon REAL,
                InvSeq INT,
                Patent TEXT,
                GYear INT,
                AppYearStr TEXT,
                AppDateStr TEXT,
                Assignee TEXT,
                AsgNum INT,
                Class TEXT,
                Invnum TEXT,
                Invnum_N TEXT,
                num_subclasses INT,
                backward_cites INT,
                forward_cites INT,
                totalInventors INT,
                betweenness REAL,
                eigenvector_centrality REAL,
                node_constraint REAL,
                degree INT,
                component INT,
                clustering_coefficient REAL
            );
            CREATE INDEX idx_invnumN on invpat_temp(invnum_N);
            CREATE INDEX inx_patent on invpat_temp(patent);
            """)
            snippet = self.data['invpat'].c.execute("""select firstname, lastname, street, city, state, country, zipcode, lat, lon, invseq, patent,
                gyear, appyearstr, appdatestr, assignee, asgnum, class, invnum, invnum_N, num_subclasses, backward_cites, forward_cites, totalInventors
                from invpat where appyearstr between %d AND %d""" % (year, year+2)).fetchall()
            conn.executemany("""INSERT INTO invpat_temp (firstname, lastname, street, city, state, country, zipcode, lat, lon, invseq, patent, gyear, appyearstr, appdatestr, assignee, asgnum, class,
                  invnum, invnum_N, num_subclasses, backward_cites, forward_cites, totalInventors) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", snippet)
            # plus the network measures
            n = []
            for i in self.graphs[year].vs:
                n.append((i['degree'], i['constraint'], i['component'], i['eigenvector_centrality'], i['clustering_coefficient'], i['inventor_id']))
            conn.executemany("""UPDATE invpat_temp SET degree = ?, node_constraint = ?, component = ?, eigenvector_centrality = ?,
                             clustering_coefficient = ? WHERE Invnum_N = ?""", n)
            conn.commit()
            
            # write the temp table to the file
            fname = self.filepath + "invpat{year}.csv".format(year=year)
            print "Creating {f}".format(f=fname)
            f = open(fname, "wb")
            writer = csv.writer(f, lineterminator="\n")
            writer.writerows([[x[1] for x in conn.execute("PRAGMA table_info(invpat_temp)").fetchall()]])
            writer.writerows([asc(x) for x in conn.execute("select * from invpat_temp").fetchall()])
            writer = None
            f.close()
            conn.close()

        self.close_data()

        

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if(sys.argv[1] == 'help' or sys.argv[1] == '?'):
            print DVN_script.__doc__
        else:
            DVN_script(sys.argv[1], sys.argv[2:])
    else:
        print "Please provide database filepath or enter ? or help for more info"


