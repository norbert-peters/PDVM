# pdvm_langtext.py
# --------------------------------------------------------------------------------------------
# Hier wird das Wörterbuch für die einzelnen Sprachen nachgebildet. Am Ende können diese dann
# auch ggf. von der Datenbank gelesen werden
#
# das oberste Ordnungsmerkmal ist die Sprache. Diese wird mit dem üblichen DIN Begriff abgebildet.
# von vorn herein halte ich zwei Sprachen vor:
#   de-de --> deutsch - Deutschland
#   en-us --> englisch - USA
#
# Dazu gibt es Kategorien die in einer eigenen Kategorie vorgehalten und übersetzt werden.
#
# Es ist auch angedacht später auch die gesamte dynamische Oberfläche, die ich plane hiermit in
# unterschiedlichen Sprachen bereitzustellen. Dies betrifft dann auch die einzelnen Dropdown - Auswahlen
# die sich nicht auf ein Objekt beziehen.
#
# -------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------
# Einstellungen 
# -------------------------------------------------------------------------------------------
language = ['en-us','de-de']        # verfügbare Sprachen - Programmabbruch vermeiden
st_lanquage = 'de-de'               # Standardsprache, wenn Sprachangabe falsch ist
# -------------------------------------------------------------------------------------------

transbook = {
    'general':{
        'de-de':{
            'addition':'Addition',
            'blank':' ',
            'countryFDate':'Land für Datum',
            'diffExist':'Differenzen vorhanden',
            'diffIn':'Differenz in',
            'message':'Meldung',
            'noDiff':'Keine Differenzen vorhanden',
            'origin':'Ursprung',
            'OutTestProt': 'Ausgabe Testprotokoll',
            'ResAfterDiffAddition':'Ergebnis nach Differenzaddition',
            'testEdition':'Testausgabe', 
            'testResult':'Testergebnis',
        },
        'en-us':{
            'addition':'addition',
            'blank':' ',
            'countryFDate':'Country by Date',
            'diffExist':'Differences exist',
            'diffIn': 'Difference in',
            'message':'Message',
            'noDiff':'There are no differences',
            'origin':'origin',
            'OutTestProt': 'Output test protocol',
            'ResAfterDiffAddition':'Result after difference addition',
            'testEdition': 'Test edition',
            'testResult':'Test result',
        }
    },
    'kategory':{
        'de-de':{
            'general':'Allgemeines',
            'kategory':'Kategorie',
            'label':'Feldbeschreibung',
            'monthname':'Monatsnamen',
            'messages':'Meldungen',
            'proptext':'Bezeichnungen der Eigenschaften',
            'transYN':'ja/nein',
            'weekdays':'Wochentage',
        },
        'en-us':{
            'general':'general',
            'kategory':'kategory',
            'label':'label',
            'monthname':'monthname',
            'messages':'messages',
            'proptext':'Designations of the properties',
            'transYN':'yea/no',
            'weekdays':'weekdays',
        },
    },
    'label':{
        'de-de':{
            'birthday':'Geburtstag',
            'comment':'Kommentar',
            'created_at':'Eingefügt am',
            'first_name':'Vorname',
            'gaz':'Gültig ab Zeit',
            'is_admin':'Ist Administrator',
            'last_name':'Nachname',
            'password':'Passwort',
            'rep_password':'Passwort wiederholen',
            'updated_at':'Letztes Update',
            'username':'Benutzername',
        },
        'en-us':{
            'birthday':'birthday',
            'comment':'comment',
            'created_at':'created at',
            'first_name':'first name',
            'gaz':'Valid from time',
            'is_admin':'is administrator',
            'last_name':'last name',
            'password':'password',
            'rep_password':'Repeat password',
            'updated_at':'updated at',
            'username':'username',
        },
    },
    'monthname':{
        'de-de':{
            '1':'Januar',
            '2':'Februar',
            '3':'März',
            '4':'April',
            '5':'Mai',
            '6':'Juni',
            '7':'Juli',
            '8':'August',
            '9':'September',
            '10':'Oktober',
            '11':'November',
            '12':'Dezember',
        },
        'en-us':{
            '1':'January',
            '2':'February',
            '3':'March',
            '4':'April',
            '5':'May',
            '6':'June',
            '7':'July',
            '8':'August',
            '9':'September',
            '10':'October',
            '11':'November',
            '12':'December',
        },
    },
    'messages':{
        'de-de':{
            'ACC_001':'Das Benutzerkonto benötigt eine valide Email-Adresse!',
            'ACC_002':'Das Benutzerkonto muss eine validen Namen haben!',
            "ACC_003":"Passworte sind nicht gleich",
            "PDT_001":"Format falsch - zugelassen YYYYDDD,Zeitwert",
            "PDT_002":"Format falsch - zugelassen (YYYY,MM,DD,HH,Min,Sec,MSec)",
            "PDT_003":"Format falsch - zugelassen (YYYYDDD)",
            "PDT_004":"Format falsch - zugelassen (YYYY,MM,DD)",
            "PDT_005":"Format falsch - zugelassen (0,Zeitwert)",
            "PDT_006":"Format falsch - zugelassen (HH,Min,Sec,MSec)",
            "PDT_007":"Eingabe nicht numerisch! Splitter falsch?",
            "PDT_008":"Format Länge falsch!",
            "PDT_009":"Format kann nicht verwendet werden",
            "PDT_010":"Monat nicht möglich!",
            "PDT_011":"Der Tag ist für den Monat(Jahr) nicht möglich!",
            "PDT_012":"Länge nicht zugelassen",
            "PDT_013":"Nicht realisiertes Landformat",
            "PDT_014":"Gesplitteter Wert falsch! Splitter unterschiedlich?",
            "PLT_001":"Kein Eintrag im Wörterbuch",
            "PLT_002":"Für diese Sprache ist kein Wörterbuch verfügbar",
        },
        'en-us':{
            'ACC_001':'The user account requires a valid email address!',
            'ACC_002':'The user account must have a valid name!',
            "ACC_003":"Passwords are not the same",
            "PDT_001":"Format wrong - allowed YYYYDDD, time value",
            "PDT_002":"Format wrong - allowed (YYYY, MM, DD, HH, Min, Sec, MSec)",
            "PDT_003":"Format wrong - allowed (YYYYDDD)",
            "PDT_004":"Format wrong - allowed (YYYY, MM, DD)",
            "PDT_005":"Format wrong - allowed (0, time value)",
            "PDT_006":"Format wrong - allowed (HH, Min, Sec, MSec)",
            "PDT_007":"Entry not numerical! Splinter wrong?",
            "PDT_008":"Format length wrong!",
            "PDT_009":"Format can not be used",
            "PDT_010":"Month not possible!",
            "PDT_011":"The day is not possible for the month (year)!",
            "PDT_012":"Length not allowed",
            "PDT_013":"Unrealized land format",
            "PDT_014":"Split value wrong! Splitter different?",
            "PLT_001":"No entry in the dictionary",
            "PLT_002":"There is no dictionary available for this language",
        },
    },
    'proptext':{
        'de-de':{
            "FormCountry"         : "Landformat",
            "PdvmDateTime"        : "PDVM Datum/Zeit",
            "PdvmDateTimeNow"     : "PDVM Datum/Zeit jetzt",
            "PdvmDate"            : "PDVM Datum",
            "PdvmTime"            : "PDVM Zeit",
            "PdvmDateTimeT"       : "PDVM Datum/Zeit Tabelle",
            "PdvmDateT"           : "PDVM Datum Tabelle",
            "PdvmTimeT"           : "PDVM Zeit Tabelle",
            "Date"                : "Datum Landesform",
            "Time"                : "Zeit Landesform",
            "TimeShort"           : "Zeit Landesform kurz",
            "YDay"                : "Tag im Jahr",
            "Weekday"             : "Wochentag",
            "LYear"               : "Schaltjahr",
            "Period"              : "Monatsperiode",
            "FormTimeStamp"       : "Datum/Zeit formatierte Ausgabe",
            "TimeStamp"           : "Datum/Zeit Landesform",
            "FirstDayOfMonth"     : "erster Tag im Monat",
            "LastDayOfMonth"      : "letzter Tag im Monat",
            "FirstDayOfNextMonth" : "erster Tag nächster Monat",
            "Year"                : "Jahr",
            "Month"               : "Monat",
            "Day"                 : "Tag",
            "Days"                : "Tage",
            "Hour"                : "Stunde",
            "Hours"               : "Stunden",
            "Minute"              : "Minute",
            "Minutes"             : "Minuten",
            "Second"              : "Sekunde",
            "Seconds"             : "Sekunden",
            "DecHour"             : "Dezimal Stunde",
            "DecMin"              : "Dezimal Minute",
            "DecSec"              : "Dezimal Sekunde",
            "HourDec"             : "Stunde dezimal",
            "MinDec"              : "Minute dezimal",
        },
        'en-us':{
            "FormCountry"         : "Country form",
            "PdvmDateTime"        : "PDVM date / time",
            "PdvmDateTimeNow"     : "PDVM date / time now",
            "PdvmDate"            : "PDVM date",
            "PdvmTime"            : "PDVM time",
            "PdvmDateTimeT"       : "PDVM date / time table",
            "PdvmDateT"           : "PDVM date table",
            "PdvmTimeT"           : "PDVM time table",
            "Date"                : "date country form",
            "Time"                : "time country form",
            "TimeShort"           : "time country form short",
            "YDay"                : "day in the year",
            "Weekday"             : "weekday",
            "LYear"               : "leap-year",
            "Period"              : "month period",
            "FormTimeStamp"       : "Date / time formatted output",
            "TimeStamp"           : "date / time country form",
            "FirstDayOfMonth"     : "first day of the month",
            "LastDayOfMonth"      : "last day of the month",
            "FirstDayOfNextMonth" : "first day next month",
            "Year"                : "year",
            "Month"               : "month",
            "Day"                 : "day",
            "Days"                : "days",
            "Hour"                : "hour",
            "Hours"               : "hours",
            "Minute"              : "minute",
            "Minutes"             : "minutes",
            "Second"              : "second",
            "Seconds"             : "seconds",
            "DecHour"             : "decimal hour",
            "DecMin"              : "decimal minute",
            "DecSec"              : "decimal second",
            "HourDec"             : "hour decimal",
            "MinDec"              : "minute decimal",
        },
    }, 
    'transYN':{
        'de-de':{
            '0':'nein',
            '1':'ja',
        },
        'en-us':{
            '0':'no',
            '1':'yes',
        },
    },
    'weekdays':{
        'de-de':{
            '0':'Montag',
            '1':'Dienstag',
            '2':'Mittwoch',
            '3':'Donnerstag',
            '4':'Freitag',
            '5':'Samstag',
            '6':'Sonntag',
        },
        'en-us':{
            '0':'Monday',
            '1':'Tuesday',
            '2':'Wednesday',
            '3':'Thursday',
            '4':'Friday',
            '5':'Saturday',
            '6':'Sunday',
        }
    },

}


# --------------------------------------------------------------------
# gibt eine ganze Kategorie zurück
# --------------------------------------------------------------------
def transkate(lanq, kate):
    ret = ''
    z = 0
    for x in language:
        if x == lanq:
            z += 1
    if z == 0:
        __message('error','pdvm_lanqtext','PLT_002','Eingabe:'+lanq+' | '+kate,st_lanquage)    
        lanq = st_lanquage
    try:
        ret = transbook[kate][lanq]
    except:
        __message('error','pdvm_lanqtext','PLT_001','Eingabe:'+lanq+' | '+kate,lanq)    
    return ret

# --------------------------------------------------------------------
# gibt eine einzelne Übersetzung zurück
# --------------------------------------------------------------------
def transkateone(lanq, kate, word):
    ret = ''
    z = 0
    for x in language:
        if x == lanq:
            z += 1
    if z == 0:
        __message('error','pdvm_lanqtext','PLT_002','Eingabe:'+lanq+' | '+kate,st_lanquage)    
        lanq = st_lanquage
    try:
        ret = transbook[kate][lanq][word]
    except:
        __message('error','pdvm_lanqtext','PLT_001','Eingabe:'+lanq+' | '+kate+' | '+word,st_lanquage)    
    return ret

# --------------------------------------------------------------------
# Meldungen
# --------------------------------------------------------------------
def __message(typ,mod,num,aon,lanq):
    print("--------------Meldung----------------------")
    print("Nummer:  "+num)
    print("Art:     "+typ)
    print("Modul:   "+mod)
    print("         "+str(transkateone(lanq,'messages',num)))
    print("Hinweis: "+str(aon))
    print("-------------------------------------------")



# Hauptprogramm - Testumgebung
# --------------------------------------------------------------
if __name__=='__main__':
    import os               # Für Testbereich

    try:                    # Console wir leer gemacht
        os.system('CLS')    # for Windows
    except:
        os.system('CLEAR')  # for Unix

    print(str(transkate('de-de','mess1ages'))+'\n')
    print(str(transkate('en-en','messages'))+'\n')
    print(str(transkateone('de-de','messages','PDT_011'))+'\n')
    print(str(transkateone('en-us','mes1sages','PDT_011'))+'\n')
