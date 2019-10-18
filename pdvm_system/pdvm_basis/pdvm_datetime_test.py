# Aufbau Wörterbuch für Tests 
# Key   --> Bezeichnung des Tests
# tlog --> Anzeigebereich 0 -> Detail nach init         // 1 -> Details beim Werte setzen
#                         2 -> Detail bei Additionen    // 3 -> Print Tesdaten im Log
#                         4 -> Print Testdaten am Ende  // 5 -> Details bei formatierter Ausgabe
#                         6 -> Log ausgeben / Fehler werden immer ausgegeben
# tins --> Eingabewert
# tset --> Property an die der Wert übergeben wird
# tget --> Objekt.Property von der das Ergebnis kommt
# DIN  --> Ergebnis bei diesem FormCountry (wird ein Fehler erwartet, dann Ergebnis wie bei tset)
# DEU  --> Ergebnis bei diesem FormCountry (wird ein Fehler erwartet, dann Ergebnis wie bei tset)
# ENG  --> Ergebnis bei diesem FormCountry (wird ein Fehler erwartet, dann Ergebnis wie bei tset)
# USA  --> Ergebnis bei diesem FormCountry (wird ein Fehler erwartet, dann Ergebnis wie bei tset)

def testtabelle():
    tests = {
        'Test_0010': {'tlog':1, 'tins':'(2016,4,23,17,45,18,0)', 'tset':'PdvmDateTimeT', 'tget':'a.PdvmDateTime', 
            'DIN': '2016114.7397916666', 'DEU':'2016114.7397916666', 'ENG':'2016114.7397916666', 'USA':'2016114.7397916666'},

        'Test_0020': {'tlog':1, 'tins':'a.PdvmDateTimeNow()', 'tset':'PdvmDateTime', 'tget':'a.PdvmDateTime', 
            'DIN': 'a.PdvmDateTime', 'DEU':'a.PdvmDateTime', 'ENG':'a.PdvmDateTime', 'USA':'a.PdvmDateTime'},

        'Test_0030': {'tlog':1, 'tins':'a.PdvmDate+3', 'tset':'PdvmDate', 'tget':'a.PdvmDateTime', 
            'DIN': 'a.PdvmDateTime', 'DEU':'a.PdvmDateTime', 'ENG':'a.PdvmDateTime', 'USA':'a.PdvmDateTime'},

        'Test_0040': {'tlog':1, 'tins':'(2016,7,26)', 'tset':'PdvmDateT', 'tget':'a.Date', 
            'DIN': "'2016-07-26'", 'DEU':'a.Date', 'ENG':'a.Date', 'USA':'a.Date'},

        'Test_0050': {'tlog':1, 'tins':'(13,46,26,23456)', 'tset':'PdvmTimeT', 'tget':'a.PdvmTime', 
            'DIN': '0.5739123085185185', 'DEU':'0.5739123085185185', 'ENG':'0.5739123085185185', 'USA':'0.5739123085185185'},

        'Test_0060': {'tlog':1, 'tins':'a.PdvmTime', 'tset':'PdvmTime', 'tget':'a.PdvmTimeT', 
            'DIN': '(13, 46, 26, 23456)', 'DEU':'(13, 46, 26, 23456)', 'ENG':'(13, 46, 26, 23456)', 'USA':'(13, 46, 26, 23456)'},

        'Test_0065': {'tlog':1, 'tins':'2019300.345988453', 'tset':'PdvmTime', 'tget':'a.PdvmDateTimeT', 
            'DIN': '(0, 0, 0, 8, 18, 13, 402330)', 'DEU':'(0, 0, 0, 8, 18, 13, 402330)', 'ENG':'(0, 0, 0, 8, 18, 13, 402330)', 'USA':'(0, 0, 0, 8, 18, 13, 402330)'},

        'Test_0070': {'tlog':1, 'tins':'(2016,12,31,7,20,19,0)', 'tset':'PdvmDateTimeT', 'tget':'a.PdvmDateTime', 
            'DIN': '2016366.3057754629', 'DEU':'2016366.3057754629', 'ENG':'2016366.3057754629', 'USA':'2016366.3057754629'},

        'Test_0080': {'tlog':2, 'tins':'a.PdvmDate', 'tset':'PdvmDate', 'tget':'a.AddMonthPeriod(3)', 
            'DIN': '201703', 'DEU':'201703', 'ENG':'201703', 'USA':'201703'},

        'Test_0090': {'tlog':2, 'tins':'a.PdvmDate', 'tset':'PdvmDate', 'tget':'a.AddYearPeriod(2)', 
            'DIN': '201812', 'DEU':'201812', 'ENG':'201812', 'USA':'201812'},

        'Test_0100': {'tlog':2, 'tins':'a.PdvmDate', 'tset':'PdvmDate', 'tget':'a.AddYear(2)', 
            'DIN': '2018365.0', 'DEU':'2018365.0', 'ENG':'2018365.0', 'USA':'2018365.0'},

        'Test_0110': {'tlog':2, 'tins':'a.PdvmDate', 'tset':'PdvmDate', 'tget':'a.AddMonth(3)', 
            'DIN': '2019090.0', 'DEU':'2019090.0', 'ENG':'2019090.0', 'USA':'2019090.0'},

        'Test_0120': {'tlog':2, 'tins':'a.PdvmDate', 'tset':'PdvmDate', 'tget':'a.AddDay(30)', 
            'DIN': '2019120.0', 'DEU':'2019120.0', 'ENG':'2019120.0', 'USA':'2019120.0'},

        'Test_0130': {'tlog':2, 'tins':'(2017,1,1,13,10,50,0)', 'tset':'PdvmDateTimeT', 'tget':'a.PdvmDateTime', 
            'DIN': '2017001.5491898148', 'DEU':'2017001.5491898148', 'ENG':'2017001.5491898148', 'USA':'2017001.5491898148'},

        'Test_0140': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddMonthPeriod(-14)', 
            'DIN': '201511', 'DEU':'201511', 'ENG':'201511', 'USA':'201511'},

        'Test_0150': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddYearPeriod(-20)', 
            'DIN': '199701', 'DEU':'199701', 'ENG':'199701', 'USA':'199701'},

        'Test_0160': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddYear(-20)', 
            'DIN': '1997001.5491898148', 'DEU':'1997001.5491898148', 'ENG':'1997001.5491898148', 'USA':'1997001.5491898148'},

        'Test_0170': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddMonth(-14)', 
            'DIN': '1995305.5491898148', 'DEU':'1995305.5491898148', 'ENG':'1995305.5491898148', 'USA':'1995305.5491898148'},

        'Test_0180': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddDay(-114)', 
            'DIN': '1995191.5491898148', 'DEU':'1995191.5491898148', 'ENG':'1995191.5491898148', 'USA':'1995191.5491898148'},

        'Test_0190': {'tlog':2, 'tins':'a.PdvmDateTimeNow()', 'tset':'PdvmDateTime', 'tget':'a.PdvmDateTime', 
            'DIN': 'a.PdvmDateTime', 'DEU':'a.PdvmDateTime', 'ENG':'a.PdvmDateTime', 'USA':'a.PdvmDateTime'},

        'Test_0200': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddMonthPeriod(-4)', 
            'DIN': 'a.Period-4', 'DEU':'a.Period-4', 'ENG':'a.Period-4', 'USA':'a.Period-4'},

        'Test_0210': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddYearPeriod(-2)', 
            'DIN': 'a.Period-200', 'DEU':'a.Period-200', 'ENG':'a.Period-200', 'USA':'a.Period-200'},

        'Test_0220': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddYear(-2)', 
            'DIN': 'a.PdvmDateTime-2000', 'DEU':'a.PdvmDateTime-2000', 'ENG':'a.PdvmDateTime-2000', 'USA':'a.PdvmDateTime-2000'},

        'Test_0230': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddMonth(-4)', 
            'DIN': 'a.PdvmDateTime-tag_4mon', 'DEU':'a.PdvmDateTime-tag_4mon', 'ENG':'a.PdvmDateTime-tag_4mon', 'USA':'a.PdvmDateTime-tag_4mon'},

        'Test_0240': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddDay(-14)', 
            'DIN': 'a.PdvmDateTime-14', 'DEU':'a.PdvmDateTime-14', 'ENG':'a.PdvmDateTime-14', 'USA':'a.PdvmDateTime-14'},

        'Test_0250': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddHour(100)', 
            'DIN': 'a.PdvmDateTime+4.1666666667', 'DEU':'a.PdvmDateTime+4.1666666667', 'ENG':'a.PdvmDateTime+4.1666666667', 'USA':'a.PdvmDateTime+4.1666666667'},

        'Test_0260': {'tlog':2, 'tins':'a.PdvmDateTime', 'tset':'PdvmDateTime', 'tget':'a.AddSecond(90)', 
            'DIN': 'a.PdvmDateTime+0.0010416667', 'DEU':'a.PdvmDateTime+0.0010416667', 'ENG':'a.PdvmDateTime++0.0010416667', 'USA':'a.PdvmDateTime++0.0010416667'},

        'Test_0270': {'tlog':5, 'tins':"'191,14'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': 'a.Date', 'DEU':'a.Date', 'ENG':'a.Date', 'USA':'a.Date'},

        'Test_0280': {'tlog':5, 'tins':"'201911130'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': 'a.Date', 'DEU':'a.Date', 'ENG':'a.Date', 'USA':'a.Date'},

        'Test_0290': {'tlog':5, 'tins':"'20191'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': 'a.Date', 'DEU':'a.Date', 'ENG':'a.Date', 'USA':'a.Date'},

        'Test_0300': {'tlog':5, 'tins':"'190823'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': "'2019-08-23'", 'DEU':"'19.08.2023'", 'ENG':"'19/08/2023'", 'USA':'a.Date'},

        'Test_0310': {'tlog':5, 'tins':"'20191130'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': "'2019-11-30'", 'DEU':'a.Date', 'ENG':'a.Date', 'USA':'a.Date'},

        # Test wird im Jahr 2021 falsch!! dynamische Berechnung - Ergebnis korrigieren
        'Test_0320': {'tlog':5, 'tins':"'250130'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': "'1925-01-30'", 'DEU':"'25.01.1930'", 'ENG':"'25/01/1930'", 'USA':'a.Date'},

        'Test_0330': {'tlog':5, 'tins':"'0203'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': "akt_year+'-02-03'", 'DEU':"'02.03.'+akt_year", 'ENG':"'02/03/'+akt_year", 'USA':"'2/3/'+akt_year"},

        'Test_0340': {'tlog':5, 'tins':"'20120229'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': "'2012-02-29'", 'DEU':"'20.12.229'", 'ENG':"'20/12/229'", 'USA':'a.Date'},

        'Test_0350': {'tlog':5, 'tins':"'0229'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': 'a.Date', 'DEU':'a.Date', 'ENG':'a.Date', 'USA':"'2/29/'+akt_year if (a.LYear == 1) else a.Date"},

        'Test_0360': {'tlog':5, 'tins':"'2020-2-29'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': "'2020-02-29'", 'DEU':'a.Date', 'ENG':'a.Date', 'USA':'a.Date'},

        'Test_0370': {'tlog':5, 'tins':"'23.5.2018'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': 'a.Date', 'DEU':"'23.05.2018'", 'ENG':"'23/05/2018'", 'USA':'a.Date'},

        'Test_0380': {'tlog':5, 'tins':"'2019/8/5'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': "'2019-08-05'", 'DEU':'a.Date', 'ENG':'a.Date', 'USA':'a.Date'},

        'Test_0390': {'tlog':5, 'tins':"'09/07/2021'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': 'a.Date', 'DEU':"'09.07.2021'", 'ENG':"'09/07/2021'", 'USA':"'9/7/2021'"},

        'Test_0400': {'tlog':5, 'tins':"'-090721'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': "'2009-07-21'", 'DEU':"'09.07.2021'", 'ENG':"'09/07/2021'", 'USA':"'9/7/2021'"},

        'Test_0410': {'tlog':5, 'tins':"'-9-07-21'", 'tset':'Date', 'tget':'a.Date', 
            'DIN': "'9-07-21'", 'DEU':"'09.07.21'", 'ENG':"'09/07/21'", 'USA':"'9/7/21'"},

        'Test_0420': {'tlog':5, 'tins':"'125313'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': "'12:53:13'", 'DEU':"'12:53:13'", 'ENG':"'12:53:13'", 'USA':"'12:53:13 PM'"},

        'Test_0430': {'tlog':5, 'tins':"'07031'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': 'a.Time', 'DEU':'a.Time', 'ENG':'a.Time', 'USA':'a.Time'},

        'Test_0440': {'tlog':5, 'tins':"'0703'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': "'07:03:00'", 'DEU':"'07:03:00'", 'ENG':"'07:03:00'", 'USA':"'7:03:00 AM'"},

        'Test_0450': {'tlog':5, 'tins':"'18'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': "'18:00:00'", 'DEU':"'18:00:00'", 'ENG':"'18:00:00'", 'USA':"'6:00:00 PM'"},

        'Test_0460': {'tlog':5, 'tins':"'181'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': 'a.Time', 'DEU':'a.Time', 'ENG':'a.Time', 'USA':'a.Time'},

        'Test_0470': {'tlog':5, 'tins':"'12:23:13'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': "'12:23:13'", 'DEU':"'12:23:13'", 'ENG':"'12:23:13'", 'USA':"'12:23:13 PM'"},

        'Test_0480': {'tlog':5, 'tins':"'12,23,52'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': "'12:23:52'", 'DEU':"'12:23:52'", 'ENG':"'12:23:52'", 'USA':"'12:23:52 PM'"},

        'Test_0490': {'tlog':5, 'tins':"'6.3:3'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': "'06:03:03'", 'DEU':"'06:03:03'", 'ENG':"'06:03:03'", 'USA':"'6:03:03 AM'"},

        'Test_0500': {'tlog':5, 'tins':"'6.3.3'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': "'06:03:03'", 'DEU':"'06:03:03'", 'ENG':"'06:03:03'", 'USA':"'6:03:03 AM'"},

        'Test_0510': {'tlog':5, 'tins':"'6.3'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': "'06:03:00'", 'DEU':"'06:03:00'", 'ENG':"'06:03:00'", 'USA':"'6:03:00 AM'"},

        'Test_0520': {'tlog':5, 'tins':"'12-23-13'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': 'a.Time', 'DEU':'a.Time', 'ENG':'a.Time', 'USA':'a.Time'},

        'Test_0530': {'tlog':5, 'tins':"'12,'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': "'12:00:00'", 'DEU':"'12:00:00'", 'ENG':"'12:00:00'", 'USA':"'12:00:00 PM'"},

        'Test_0540': {'tlog':5, 'tins':"'18.3'", 'tset':'Time', 'tget':'a.Time', 
            'DIN': "'18:03:00'", 'DEU':"'18:03:00'", 'ENG':"'18:03:00'", 'USA':"'6:03:00 PM'"},

        # Neues aktuelles Datum setzen - für nachfolgende Berechnung
        'Test_0550': {'tlog':1, 'tins':'a.PdvmDateTimeNow()', 'tset':'PdvmDateTime', 'tget':'a.PdvmDateTime', 
            'DIN': 'a.PdvmDateTime', 'DEU':'a.PdvmDateTime', 'ENG':'a.PdvmDateTime', 'USA':'a.PdvmDateTime'},
    }

    return tests
