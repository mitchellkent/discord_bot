import sqlite3
from sqlite3 import Error
database = "./points.db"

#   Create a table that holds all new data, cycles through all tables, adds their data to the new table, then deletes them all.
def migrate_tables(conn):
    
    #Create new master table
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS UserData (id INTEGER,link text,points INTEGER,date text)")
    conn.commit()

    #Select all user table names to cycle through
    cur = conn.cursor()
    cur.execute("SELECT name from sqlite_master where type= 'table' AND name NOT IN ('leaderboard','sqlite_sequence','UserData')")
    tables = cur.fetchall()

    for table in tables:
        print(table)

        #selects all user submitions
        query = "SELECT {} AS id,link,0 As POINTS,datetime('now') AS date FROM '{}'".format(int(table[0]),table[0])
        print(query)
        cur = conn.cursor()
        cur.execute(query)
        tableInfo = cur.fetchall()

        for info in tableInfo:
            print(info)

        #Insert all user submitions into new table
        query = "INSERT INTO UserData SELECT {} AS id,link,0 As POINTS,datetime('now') AS date FROM '{}';".format(int(table[0]),table[0])
        print(query)
        cur = conn.cursor()
        cur.execute(query)

        #Get user leaderboard score
        query = "SELECT points FROM leaderboard WHERE user='{}' LIMIT 1".format(table[0])
        cur = conn.cursor()
        cur.execute(query)
        points = cur.fetchall()

        #Set first submition of user to be their leaderboard score, this means only one of their submitions will have points after migration
        query = "UPDATE UserData SET points = {} WHERE id='{}' AND link = '{}'".format(int(points[0][0]),table[0],tableInfo[0][1])
        print(query)
        cur = conn.cursor()
        cur.execute(query)

        for tableInfoRow in tableInfo:
            print('     {}'.format(tableInfoRow))

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
    query = "Select id, sum(points) AS pointCount FROM UserData GROUP BY id ORDER BY pointCount DESC LIMIT 20"
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