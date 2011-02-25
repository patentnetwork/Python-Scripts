#http://earth-info.nga.mil/gns/html/gis_countryfiles.htm
#http://geonames.usgs.gov/domestic/download_data.htm

import datetime, csv, os, re, sqlite3, unicodedata
from locFunc import uniasc, cityctry

cc_iso = {'BD': 'BM', 'BF': 'BS', 'BG': 'BD', 'BA': 'BH', 'WA': 'NA', 'BC': 'BW', 'BL': 'BO', 'BN': 'BJ', 'BO': 'BY', 'BH': 'BZ', 'WI': 'EH', 'BK': 'BA', 'BU': 'BG', 'BP': 'SB', 'TP': 'ST', 'BX': 'BN', 'BY': 'BI', 'RP': 'PH', 'RS': 'RU', 'TL': 'TK', 'RM': 'MH', 'RI': 'RS', 'TK': 'TC', 'GV': 'GN', 'GG': 'GE', 'GB': 'GA', 'GA': 'GM', 'GM': 'DE', 'GK': 'GG', 'GJ': 'GD', 'SV': 'SJ', 'HO': 'HN', 'HA': 'HT', 'PS': 'PW', 'PP': 'PG', 'PU': 'GW', 'JA': 'JP', 'PC': 'PN', 'PA': 'PY', 'PO': 'PT', 'PM': 'PA', 'EN': 'EE', 'EI': 'IE', 'ZI': 'ZW', 'EK': 'GQ', 'ZA': 'ZM', 'EZ': 'CZ', 'AN': 'AD', 'ES': 'SV', 'UP': 'UA', 'MG': 'MN', 'MF': 'YT', 'MA': 'MG', 'MC': 'MO', 'MB': 'MQ', 'MO': 'MA', 'MN': 'MC', 'MI': 'MW', 'MH': 'MS', 'MJ': 'ME', 'MU': 'OM', 'MP': 'MU', 'UK': 'GB', 'VT': 'VA', 'FP': 'PF', 'FS': 'TF', 'FG': 'GF', 'NH': 'VU', 'NI': 'NG', 'NE': 'NU', 'NG': 'NE', 'NS': 'SR', 'NT': 'AN', 'NU': 'NI', 'CK': 'CC', 'CJ': 'KY', 'CI': 'CL', 'CH': 'CN', 'CN': 'KM', 'CB': 'KH', 'CG': 'CD', 'CF': 'CG', 'CE': 'LK', 'CD': 'TD', 'CS': 'CR', 'CW': 'CK', 'CT': 'CF', 'SZ': 'CH', 'SX': 'GS', 'SP': 'ES', 'SW': 'SE', 'KN': 'KP', 'SU': 'SD', 'ST': 'LC', 'KS': 'KR', 'KR': 'KI', 'SN': 'SG', 'KU': 'KW', 'KT': 'CX', 'SC': 'KN', 'SB': 'PM', 'SG': 'SN', 'SF': 'ZA', 'SE': 'SC', 'DO': 'DM', 'UV': 'BF', 'YM': 'YE', 'DA': 'DK', 'DR': 'DO', 'LG': 'LV', 'LE': 'LB', 'TX': 'TM', 'LO': 'SK', 'TT': 'TL', 'TU': 'TR', 'TS': 'TN', 'LH': 'LT', 'LI': 'LR', 'TN': 'TO', 'TO': 'TG', 'LT': 'LS', 'LS': 'LI', 'TI': 'TJ', 'TD': 'TT', 'AA': 'AW', 'AC': 'AG', 'IZ': 'IQ', 'AG': 'DZ', 'VI': 'VG', 'IS': 'IL', 'AJ': 'AZ', 'WZ': 'SZ', 'VM': 'VN', 'IV': 'CI', 'AS': 'AU', 'AU': 'AT', 'AV': 'AI', 'IC': 'IS'}

flder = "GNS"
#returns the latest file..
fname = sorted([x for x in os.listdir(flder)])[-1]

flderUS = "SASZip"
fnameUS = [x for x in os.listdir(flderUS) if re.search(r'[.]csv', x, re.I)!=None]

conn = sqlite3.connect("loctbl.sqlite3")
c = conn.cursor()

#http://www.sqlite.org/faq.html#q7
#tbls = [x[0] for x in c.execute("select name from sqlite_master where type='table'")]
c.executescript("""
    CREATE TABLE IF NOT EXISTS gnsloc (
        RC INTEGER,
        UFI INTEGER,        UNI INTEGER,
        LAT FLOAT,          LONG FLOAT,
        DMS_LAT INTEGER,    DMS_LONG INTEGER,
        MGRS VARCHAR(15),   JOG VARCHAR(7),
        FC VARCHAR(1),      DSG VARCHAR(5),
        PC INTEGER,         CC1 VARCHAR(2),
        ADM1 VARCHAR(2),    ADM2 VARCHAR(2),
        POP INTEGER,        ELEV INTEGER,
        CC2 VARCHAR(2),     NT VACRHAR(1),
        LC VARCHAR(3),      SHORT_FORM VARCHAR(10),
        GENERIC VARCHAR(15),SORT_NAME VARCHAR(15),
        FULL_NAME VARCHAR(15),
        FULL_NAME_ND VARCHAR(15),
        MODIFY_DATE VARCHAR(10),
        SORT_NAME3 VARCHAR(3),
        SORT_NAME4R VARCHAR(3),
        UNIQUE(RC, CC1, ADM1, ADM2, CC2, SORT_NAME));
    CREATE INDEX IF NOT EXISTS idx_all  ON gnsloc (RC, CC1, ADM1, ADM2, CC2, SORT_NAME);
    """)

f = open(flder+"/"+fname, "r")
print f.readline()
j = 0
for i,x in enumerate(f):
    rec = x.split("\t")
##    if rec[9]=="P" and rec[11]!="": #if Unknown, super small right?
##    if rec[9]=="P":
        #properly adjust country code
    if rec[12] in cc_iso:
        rec[12] = cc_iso[rec[12]]
    rec[22] = uniasc(unicode(rec[22], "latin-1")).upper()
    rec[23] = uniasc(unicode(rec[23], "latin-1")).upper()
    rec[24] = uniasc(unicode(rec[24], "latin-1")).upper()
    rec[25] = rec[25][:-1]
    rec.extend([rec[22].upper()[:3], rec[22].upper()[::-1][:4]])
    c.execute("INSERT OR REPLACE INTO gnsloc VALUES (%s)" % ",".join(["?"]*28), rec)
    if i%100000==0:
        conn.commit()
        print i, datetime.datetime.now()
        j = 0
##    if i==50000:
##        break
conn.commit()

print "INDEXING - BASIC"
c.executescript("""
    CREATE INDEX IF NOT EXISTS idx_rc   ON gnsloc (RC);
    CREATE INDEX IF NOT EXISTS idx_cc1  ON gnsloc (CC1);
    CREATE INDEX IF NOT EXISTS idx_cc2  ON gnsloc (CC2);
    CREATE INDEX IF NOT EXISTS idx_adm1 ON gnsloc (ADM1);
    CREATE INDEX IF NOT EXISTS idx_adm2 ON gnsloc (ADM2);
    CREATE INDEX IF NOT EXISTS idx_fc   ON gnsloc (FC);
    """)
print "INDEXING - COMBO"
c.executescript("""
    CREATE INDEX IF NOT EXISTS idx_ctc0 ON gnsloc (SORT_NAME, CC1);
    CREATE INDEX IF NOT EXISTS idx_ctc1 ON gnsloc (FULL_NAME, CC1);
    CREATE INDEX IF NOT EXISTS idx_ctc2 ON gnsloc (FULL_NAME_ND, CC1);
    CREATE INDEX IF NOT EXISTS idx_ct3  ON gnsloc (SORT_NAME3,  CC1);
    CREATE INDEX IF NOT EXISTS idx_ct4r ON gnsloc (SORT_NAME4R, CC1);
    CREATE INDEX IF NOT EXISTS idx_ctsf ON gnsloc (SHORT_FORM, CC1);
    """)

#US LOC
c.executescript("""
    CREATE TABLE IF NOT EXISTS usloc (
        Zipcode INTEGER,
        Lat FLOAT,          Long FLOAT,
        City VARCHAR(10),   State VARCHAR(2),
        StateName VARCHAR(10),
        UNIQUE(Zipcode, City, State));
    CREATE INDEX IF NOT EXISTS uidx_all ON usloc (Zipcode, City, State);
    CREATE INDEX IF NOT EXISTS uidx_zip ON usloc (Zipcode);
    CREATE INDEX IF NOT EXISTS uidx_cty ON usloc (City);
    CREATE INDEX IF NOT EXISTS uidx_st  ON usloc (State);
    """)

for x in fnameUS:
    c.executemany("INSERT OR REPLACE INTO usloc VALUES (?,?,?,?,?,?)", [x for x in csv.reader(open("%s/%s" % (flderUS, x), "r"))][1:])

#TYPOS
typos = [[cityctry(x[0], x[2]), x[1], cityctry(x[0], x[2], ret="ctry"),
          uniasc(unicode(x[3], "latin-1")).upper(), x[4], x[5]]
         for x in csv.reader(open("Typos\Typos.csv", "rb"))][1:]

c.executescript("""
    DROP TABLE IF EXISTS typos;
    CREATE TABLE IF NOT EXISTS typos (
        City VARCHAR,       State VARCHAR,      Country VARCHAR,
        NewCity VARCHAR,    NewState VARCHAR,   NewCountry VARCHAR,
        UNIQUE(City, State, Country));
    CREATE INDEX IF NOT EXISTS typos_all   ON typos (City, State, Country);
    CREATE INDEX IF NOT EXISTS typos_ctry  ON typos (Country);
    CREATE INDEX IF NOT EXISTS typos_ctate ON typos (City, State);
    CREATE INDEX IF NOT EXISTS typos_cctry ON typos (City, Country);
    """)
c.executemany("INSERT OR REPLACE INTO typos VALUES (?, ?, ?, ?, ?, ?)", typos)

conn.commit()
c.close()
conn.close()
