import sqlite3

db_path = "C:/Users/norbe/OneDrive/Dokumente/Versuche/"

verbindung = sqlite3.connect(db_path + "geburtstage.db")
zeiger = verbindung.cursor()

zeiger.execute("SELECT nachname, geburtstag FROM personen")
inhalt = zeiger.fetchall()
print(inhalt)


verbindung.close()