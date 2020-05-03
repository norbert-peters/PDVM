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
from django.conf import settings            # Standardeinstellungen immer aus den Settings
# -------------------------------------------------------------------------------------------
# Einstellungen 
# -------------------------------------------------------------------------------------------
language = ['en-us','de-de']                # verfügbare Sprachen - Programmabbruch vermeiden
try:
    st_language = settings.LANGUAGE_CODE    # Standardsprache, wenn Sprachangabe falsch ist oder fehlt
except:
    st_language = 'de-de'    
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
            'modul':'Modul',
            'note':'Hinweis',
            'number':'Nummer',
            'password':'Passwort',
            'rep_password':'Passwort wiederholen',
            'typ':'Art',
            'updated_at':'Letztes Update',
            'username':'Benutzername',
        },
        'en-us':{
            'birthday':'Birthday',
            'comment':'Comment',
            'created_at':'Created at',
            'first_name':'First name',
            'gaz':'Valid from time',
            'is_admin':'Is administrator',
            'last_name':'Last name',
            'modul':'Modul',
            'note':'Note',
            'number':'Number',
            'password':'Password',
            'rep_password':'Repeat password',
            'typ':'Typ',
            'updated_at':'Updated at',
            'username':'Username',
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
            "PDU_001":"Eingabezeichen ist nicht zugelassen!",
            "PLT_001":"Kein Eintrag im Wörterbuch",
            "PLT_002":"Für diese Sprache ist kein Wörterbuch verfügbar",
            "PLT_003":"Keine Kategorie ausgewählt",
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
            "PDU_001":"Input character is not allowed!",
            "PLT_001":"No entry in the dictionary",
            "PLT_002":"There is no dictionary available for this language",
            "PLT_003":"No category selected",
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
            "TimeAll"             : "vollständige Zeit",
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
            "GetAYear"            : "aktuelles Jahr",
            "GetAYear2"           : "aktuelles Jahr zweistellig",
            "GetAYearH2"          : "aktuelles Jahrhundert zweistellig",
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
            "TimeAll"             : "complete time",
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
            "GetAYear"            : "current year",
            "GetAYear2"           : "current year double digits",
            "GetAYearH2"          : "current century double digits",
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
def transkate(kate='kategory', lang=st_language):
    ret = ''
    z = 0
    for x in language:
        if x == lang:
            z += 1
    if z == 0:
        printMessage('error','pdvm_langtext','PLT_002','Eingabe:'+lang+' | '+kate,st_language)    
        lang = st_language
    try:            # Sprache nicht vorhanden -- wird nach Fehlermeldung in Standardsprache ausgegeben
        ret = transbook[kate][lang]
    except:
        printMessage('error','pdvm_langtext','PLT_001','Eingabe:'+lang+' | '+kate,lang)    
    return ret

# --------------------------------------------------------------------
# gibt eine einzelne Übersetzung zurück
# --------------------------------------------------------------------
def transkateone(kate='messages', word='PLT003', lang=st_language):
    ret = ''
    z = 0
    for x in language:
        if x == lang:
            z += 1
    if z == 0:
        printMessage('error','pdvm_langtext','PLT_002','Eingabe:'+lang+' | '+kate,st_language)    
        lang = st_language
    try:
        ret = transbook[kate][lang][word]
    except:
        printMessage('error','pdvm_langtext','PLT_001','Eingabe:'+lang+' | '+kate+' | '+word,st_language)    
    return ret

# --------------------------------------------------------------------
# Meldungen kann hier nicht aus pdvm_util verwendet werden (Rekursion)
# --------------------------------------------------------------------
def printMessage(typ,mod,num,aon=' ',lang=st_language):
    la = 70
    li = '10'
    h_line = lockedWritten(transkateone('general', 'message', lang))
    h_mh = int((la - len(h_line) - 2) / 2)
    h_line = ' '+h_line+' '
    print(multiChar('=',h_mh)+h_line+multiChar('=',h_mh))
    print(transStringOne (lang, 'label', 'number', li)+":  "+num)
    print(transStringOne (lang, 'label', 'typ', li)+":  "+typ)
    print(transStringOne (lang, 'label', 'modul', li)+":  "+mod)
    print(stringToLength('',str(int(li)+3))+str(transkateone('messages',num, lang)))
    print(transStringOne (lang, 'label', 'note', li)+":  "+str(aon))
    print(multiChar("=",la,0))

# --------------------------------------------------------------------
# String gesperrt zurückgeben - geht nicht aus pdvm_util
# --------------------------------------------------------------------
def lockedWritten(word):
    ret = ''
    for b in word:
        ret = ret+b+' '
    return ret 

# --------------------------------------------------------------------
# gibt ein Zeichen (string) mehrfach aus - kann nicht aus pdvm_util genommen werden
# --------------------------------------------------------------------
# lf --> linefeed  // lf = 0 --> kein lf
# lf = 1 --> lf vorne  // lf = 2 --> lf hinten  // lf = 3 --> vorne und hinten
# --------------------------------------------------------------------
def multiChar(char,multi,lf=0):
    ret = char * multi
    if lf == 1 or lf == 3:
        ret = '\n'+ret
    if lf == 2 or lf == 3:
        ret = ret+'\n'
    return ret

# --------------------------------------------------------------------
# übersetzte String 'pdvmstr' mit Kategorie 'pdvmkat' auf die Länge 'pdvml' 
# direkt aus dem Wörterbuch mit der Sprache 'lang'
# -- kann nicht aus pdvm_util genommen werden
# --------------------------------------------------------------------
def transStringOne (lang, pdvmkat, pdvmstr, pdvml):
    vstr = transkateone(pdvmkat, pdvmstr, lang)
    ret =('{:<'+pdvml+'}').format(vstr)
    return ret

# --------------------------------------------------------------------
# String auf die Länge pdvml konvertieren -- kann nicht aus pdvm_util genommen werden
# --------------------------------------------------------------------
def stringToLength (pdvmstr, pdvml):
    ret =('{:<'+pdvml+'}').format(pdvmstr)
    return ret

# --------------------------------------------------------------------
# Hauptprogramm - Testumgebung
# --------------------------------------------------------------------
if __name__=='__main__':
    import os               # Für Testbereich

    try:                    # Console wir leer gemacht
        os.system('CLS')    # for Windows
    except:
        os.system('CLEAR')  # for Unix

    print(str(transkate('messages', 'de-de'))+'\n')
    print(str(transkate('messages', 'en-en'))+'\n')
    print(str(transkate('messages', 'en-us'))+'\n')
    print(str(transkateone('messages','PDT_011', 'de-de'))+'\n')
    print(str(transkateone('messages','PDT_011', 'en-us'))+'\n')
