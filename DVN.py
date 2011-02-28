import sys, SQLite, igraph, csv

class DVN():
    """
    initialize a DVN object for uploading patent data to the IQSS DVN
    """

    def __init__(self, *dbnames):
        data = {}
        graphs = {}
        for dbname in dbnames:
            data[dbname] = SQLite.SQLite(db = dbname + '.sqlite3')
        

    def create_network_file(self, begin = 2000, end = 2003, increment = 3):
        """
        create graphML files from the inventor-patent dataset
        for upload to DVN interface (by application year)

        inherits the igraph function from the patent team SQLite library
        """
        data['invpat'].chgTbl('invpat')
        for year in range(begin, end, increment):
            print "Creating file for {year}".format(year=year)
            graphs[year] = data['invpat'].igraph(where='AppYearStr BETWEEN %d AND %d and Lastname < "G"' %
                                  (year, year+2), vx="invnum_N").g

    def calculate_node_betweenness(self):
        """calculate betweenness for each node in the network all networks"""
        for g in graphs:
            g.vs["degree"] = g.degree()

    def calculate_eigenvector_centrality(self):
        """calculate eigenvector (bonacich) centrality for each node all networks"""
        for g in graphs:
            g.vs["eigenvector_centrality"] = g.eigenvector_centrality()

    def calculate_constraint(self):
        """calculate constraint for each node in all networks
        """
        for g in graphs:
            g.vs["constraint"] = g.constraint()

    def create_csv_file(self):
        """
        create csv data file for upload to DVN interface
        step 1: create database table with all relevant entries
        step 2: export to csv format
        """
        pass


