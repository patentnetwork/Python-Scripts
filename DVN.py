import sys, SQLite, igraph, csv, senGraph

# Option 1: run the script directly from the command line
# TODO: implement this!
def DVN_script(filepath = "/home/ayu/DVN", dbnames = []):
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
                - centrality (degree, betweenness, eigenvector)
                - clustering coefficient
                - constraint
                - pagerank
                - component number
            edge measures:
                - betweenness
    
    """
    print filepath
    print dbnames
    D = DVN(filepath, dbnames)
    D.summary()
    D.create_graphs()
    D.summary()
    #D.create_graphml_file(filepath, '2000')
    print "DONE"
    

# Option 2: run interactively in Python
# create a DVN object, various functions available within to use and reuse

class DVN():
    """
    initialize a DVN object for uploading patent data to the IQSS DVN
    """

    def __init__(self, filepath, dbnames):
        self.data = {}
        self.graphs = {}
        for dbname in dbnames:
            self.data[dbname] = SQLite.SQLite(filepath + dbname + '.sqlite3', dbname)
        

    def create_graphs(self, begin = 2000, end = 2006, increment = 3):
        """
        create graphML files from the inventor-patent dataset
        for upload to DVN interface (by application year)

        inherits the igraph function from the patent team SQLite library
        """
        for year in range(begin, end, increment):
            print "Creating graph for {year}".format(year=year)
            self.graphs[year] = self.data['invpat'].igraph(where='AppYearStr BETWEEN %d AND %d and Lastname < "G"' %
                                  (year, year+2), vx="invnum_N").g

    def calculate_node_betweenness(self):
        """calculate betweenness for each node in the network all networks"""
        for g in self.graphs.itervalues():
            g.vs['betweenness'] = g.betweenness()

    def calculate_eigenvector_centrality(self):
        """calculate eigenvector centrality for each node all networks"""
        # this may cause issues - getting segmentation fault previously
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

    def calculate_PageRank(self):
        """calculate pagerank for each node in all networks"""
        for g in self.graphs.itervalues():
            g.vs['PageRank'] = g.pagerank()

    def calculate_edge_betweenness(self):
        """calculate edge betweennness for all edges
        """
        for g in self.graphs.itervalues():
            g.es['betweenness'] = g.edge_betweenness()

    def get_graph(self, year):
        """returns the igraph object for the given year
        """
        return self.graphs[year]

    def create_graphml_file(self, filepath = '', year=''):
        """if year is specified, create graphml file for that specific year
        else create graphml for all years in current directory
        """
        if self.graphs.get(year):
            self.graphs[year].save((filepath + "pat_{year}.graphml").format(year=year))
        else:
            for k,v in self.graphs.iteritems():
                v.save((filepath +"pat_{year}.graphml").format(year=k))

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
                igraph.summary(v)
                print "---------------------------------------------------------"


    def create_csv_file(self):
        """
        create csv data file for upload to DVN interface
        step 1: create database table with all relevant entries
        step 2: export to csv format
        """
        pass

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if(sys.argv[1] == 'help' or sys.argv[1] == '?'):
            print DVN_script.__doc__
        else:
            DVN_script(sys.argv[1], sys.argv[2:])
    else:
        print "Please provide database filepath or enter ? or help for more info"


