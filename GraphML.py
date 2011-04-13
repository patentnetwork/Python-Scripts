import sys

sys.path.append("/home/ron/PythonBase")
import SQLite

#file = "/media/data/edward/backup/v2/final_r7.sqlite3"
file = "/home/ysun/disambig/newcode/all/invpatC.upper.Jan2011.sqlite3"

s = SQLite.SQLite(file, 'invpat')

for x in range(1975, 2010, 3):
    print x
    # Lower Bound results (currently marked as upr because we only have upr)
    s.igraph(where='AppYearStr BETWEEN %d AND %d' % (x, x+2), vx="invnum_N").g.save('/home/ayu/DVN/pat_%d_upr.graphml' % x)
    # Upper Bound results
#   s.igraph(where='AppYearStr BETWEEN %d AND %d' % (x, x), vx="new_invnum_N").g.save('pat_%d_upr.graphml' % x)

# Entire US graph for all history
s.igraph(where='Country="US"', vx="invnum_N").g.save('pat_US_upr.graphml') #changed low to upr
#s.igraph(where='Country="US"', vx="new_invnum_N").g.save('pat_US_upr.graphml')
