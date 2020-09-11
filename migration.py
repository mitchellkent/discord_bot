import sqlite3
from sqlite3 import Error
database = "./points.db"

#   Create a table that holds all new data, cycles through all tables, adds their data to the new table, then deletes them all.
def migrate_tables(conn):
    
    #Create new master table
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS UserData (id INTEGER PRIMARY KEY AUTOINCREMENT,user INTEGER,link text,points INTEGER,date text)")
    conn.commit()

    #Select all user table names to cycle through
    cur = conn.cursor()
    cur.execute("SELECT name from sqlite_master where type= 'table' AND name NOT IN ('leaderboard','sqlite_sequence','UserData','')")
    tables = cur.fetchall()

    #cycles through each table
    for table in tables:
        print(table)

        #selects all user submitions
        query = "SELECT {} AS user,link,0 As POINTS,datetime('now') AS date FROM '{}'".format(int(table[0]),table[0])
        print(query)
        cur = conn.cursor()
        cur.execute(query)
        tableInfo = cur.fetchall()
        for info in tableInfo:
            print(info)

        #Insert all user submissions into new table
        query = "INSERT INTO UserData SELECT null AS id, {} AS user,link,0 As POINTS,datetime('now') AS date FROM '{}';".format(int(table[0]),table[0])
        print(query)
        cur = conn.cursor()
        cur.execute(query)

        #Get user leaderboard score
        query = "SELECT points FROM leaderboard WHERE user='{}' LIMIT 1".format(table[0])
        cur = conn.cursor()
        cur.execute(query)
        points = cur.fetchone()

        #Insert row for users leaderboard score, this means only one of their submitions will have points after migration the rest will be zero
        query = "INSERT INTO UserData (user,link,points,date) VALUES({},{},{},datetime('now'))".format(table[0],'NULL',int(points[0]))
        print(query)
        cur = conn.cursor()
        cur.execute(query)
        for tableInfoRow in tableInfo:
            print('     {}'.format(tableInfoRow))

        #Finally, deletes user table
        query = "DROP TABLE '{}'".format(table[0])
        cur = conn.cursor()
        cur.execute(query)


    #Select all user table names to cycle through to check all have been deleted
    cur = conn.cursor()
    cur.execute("SELECT name from sqlite_master where type= 'table'")
    tables = cur.fetchall()
    #cycles through each table
    for table in tables:
        print(table)

    #This shows a quick run of what the new format would look like SQL command wise

    #Selects all data from new table
    query = "Select * FROM UserData"
    print(query)
    cur = conn.cursor()
    cur.execute(query)
    data = cur.fetchall()

    for dataRow in data:
        print('     {}'.format(dataRow))

    #Creates LeaderBoard and prints it out
    query = "Select user, sum(points) AS pointCount FROM UserData GROUP BY user ORDER BY pointCount DESC LIMIT 20"
    print(query)
    cur = conn.cursor()
    cur.execute(query)
    data = cur.fetchall()
    for dataRow in data:
        print('     {}'.format(dataRow))



con = sqlite3.connect(database)
migrate_tables(con)
con.commit()
con.close()