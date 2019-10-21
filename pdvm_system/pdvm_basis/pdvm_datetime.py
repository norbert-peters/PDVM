# pdvm_datetime.py
""" Klasse für das Zeitformat pdvmdatetime. Das Datum und die Zeit werden hier
    verwaltet. Das Datum ist eine 7-stelliger Integer (YYYYDDD), die Zeit ist
    der Prozentfaktor eines Tages hinter dem Komma. Zum Beispiel 0,5 sind
    12 Stunden bzw. 12 Uhr

    Es sind weiterhin Kalenderfunktionen bzw. Kalenderwerte in der Klasse 
    verfügbar.

    nähere Erläuterungen sind unter www.pdvm.de zu finden.

    Neu zusammengestellt:
    01.08.2019 Norbert Peters
    07.10.2019 überarbeitet
"""
# -----------------------------------------------------------------------
from numbers import Number                             # Wird zur Prüfung numerischer Werte verwendet
from pdvm_util import printMessage 
from pdvm_langtext import transkateone, transkate      # Für Übersetzung Texte
from django.conf import settings                       # Standardeinstellungen immer aus den Settings
import time                                            # Wird benutzt um die aktuelle Zeit zu ermitteln

# E i n s t e l l u n g e n
# ================================================================================
pdvmObjekt = "Pdvm_DateTime"                # Objektnamen in pdvm_system
try:
    st_language = settings.LANGUAGE_CODE    # verwendete Standardsprache
except:
    st_language = 'de-de'

try:
    st_time = settings.TIME_CODE             # verwendeter Ländercode
except:
    st_time = 'DIN'

# Anzahl der Tage einzelner Monate
monthdays = [[0,0],[0,0],[31,31],[59,60],[90,91],[120,121],[151,152],[181,182],
         [212,213],[243,244],[273,274],[304,305],[334,335],[365,366]]

# Position der Ausgabe des Datums in verschiedenen Formaten
outpos = {       
    0:{             
        1:(0,1,2),              # 0 -> Jahr // 1 -> Monat  // 2 -> Tag
        2:(0,1,2)               # Position im Datum
    },            
    2:{
        0:(1,2,0),
        1:(2,1,0),
        2:(1,2,0)
    }
}

# Position des Jahres für Splitting Eingabe
posYear = {
    8: {
        0:(0,4),2:(4,8)
    },
    6: {
        0:(0,2),2:(4,6,)
    }
}

# Position des Monats für Splitting Eingabe 
posMonth = {
    8: {
        0:(0,2),1:(2,4),2:(4,6)
    },
    6: {
        0:(0,2),1:(2,4),2:(2,4)
    },
    4: {
        0:(0,2),1:(2,4),2:(0,2)
    }
}

# Position des Tages für Splitting Eingabe 
posDay = {
    8: {
        0:(2,4),1:(0,2),2:(6,8)
    },
    6: {
        0:(2,4),1:(0,2),2:(4,6)
    },
    4: {
        0:(2,4),1:(0,2),2:(2,4)
    }
}



# -----------------------------------------------------------------------

class Pdvm_DateTime(object):

    def __init__(self,fCountry=st_time):
        # konstante Faktoren
        self._tag     = 86400000000      # Microsekunden eines Tages
        self._stunde  = 3600000000       # Microsekunden einer Stunde
        self._minute  = 60000000         # Microsekunden einer Minute
        self._sekunde = 1000000          # Microsekunden einer Sekunde
        # Aufbau Objekt mit Eigenschaften
        self.vChr          = False
        self.pdvmdatetime  = 0
        self.pdvmdate      = 0
        self.pdvmtime      = 0
        self.dd            = []
        self.dt            = []
        self.dtt           = [0,0,0]
        self.PdvmDateTimeT = [0,0,0,0,0,0,0]
        self.PdvmDateT     = [0,0,0]
        self.PdvmTimeT     = [0,0,0,0]
        self.yday          = 0
        self.period        = 0
        self.year          = 0
        self.month         = 0
        self.day           = 0
        self.hour          = 0
        self.minute        = 0
        self.second        = 0
        # Parameter auf Basis von fCountry setzen
        # Form Land vom Datum - werden als Parameter gesetzt
        self.__setFormCountry(fCountry)                             # Die Länderformen DEU / ENG / USA sind vorhanden
        self.proptext = transkate('proptext', self.language)        # Übersetzungen der Eigenschaften
                                                                    # werden als Wörterbuch eingelesen
    # --------------------------------------------------------------------
    # FormCountry
    # --------------------------------------------------------------------
    def __setFormCountry(self, fCountry):
        ckval = ['DIN', 'DEU', 'ENG', 'USA']    # weitere Formate müssen hier 
                                                # hinzugefügt werden
        dateSplitter = {'DIN': '-', 'DEU': '.', 'ENG': '/', 'USA': '/'}
        dateYearPos  = {'DIN': 0,   'DEU': 2,   'ENG': 2,   'USA': 2  }
        dateMonthPos = {'DIN': 2,   'DEU': 1,   'ENG': 1,   'USA': 0  }
        monthDayLen  = {'DIN': 2,   'DEU': 2,   'ENG': 2,   'USA': 1  }
        language_in  = {'DIN': 'st-st',   'DEU': 'de-de',   'ENG': 'en-us',   'USA': 'en-us'  }

        ok = False
        fC = fCountry.upper().strip()
        for ck in ckval:
            if ck == fC:
                ok = True
                break
            else:
                ok = False
        if ok:
            self.formCountry=fC
            self.dateSplitter  = dateSplitter[fC]
            self.dateYearPos   = dateYearPos[fC]
            self.dateMonthPos  = dateMonthPos[fC]
            self.monthDayLen   = monthDayLen[fC]
            if language_in[fC] == 'st-st':
                self.language      = st_language
            else:
                self.language      = language_in[fC]
        else:
            self.formCountry   ='DIN'      # Standardwert
            self.language      = st_language
            printMessage("error",pdvmObjekt,"PDT_013",["def: __setFormCountry","Eingabe: " + fCountry], self.language)
            self.dateSplitter  = dateSplitter['DIN']
            self.dateYearPos   = dateYearPos['DIN']
            self.dateMonthPos  = dateMonthPos['DIN']
            self.monthDayLen   = monthDayLen['DIN']

    def __getFormCountry(self):
        return self.formCountry

    FormCountry = property(__getFormCountry,__setFormCountry)

    # --------------------------------------------------------------------
    # PdvmDateTime 
    # --------------------------------------------------------------------
    def __setPdvmDateTime(self,pdvmddate):
        try:
            self.pdvmdatetime = float(pdvmddate)
            self.__pdvmDateInDateSplit()
            self.__pdvmdatime(self.year,self.month,self.day,
                            self.hour,self.minute,self.second,self.microsecond)
        except:
            printMessage("error",pdvmObjekt,"PDT_001",["def: setPdvmDateTime", "Eingabe: " + str(pdvmddate)], self.language)

    def __getPdvmDateTime(self):
        if self.vChr:
            return self.pdvmdatetime * -1
        else:
            return self.pdvmdatetime

    PdvmDateTime = property(__getPdvmDateTime,__setPdvmDateTime)

    # --------------------------------------------------------------------
    # PdvmDateTimeT 
    # --------------------------------------------------------------------
    def __setPdvmDateTimeT(self,pdvmdtt):
        try:
            self.__pdvmdatime(pdvmdtt[0],pdvmdtt[1],pdvmdtt[2],
                                           pdvmdtt[3],pdvmdtt[4],pdvmdtt[5],
                                           pdvmdtt[6])
        except:
            printMessage("error",pdvmObjekt,"PDT_002",["def: setPdvmDateTimeT", "Eingabe: " + str(pdvmdtt)], self.language)
    
    def __getPdvmDateTimeT(self):
        return self.dtt

    PdvmDateTimeT = property(__getPdvmDateTimeT,__setPdvmDateTimeT)

    # --------------------------------------------------------------------
    # PdvmDate
    # --------------------------------------------------------------------
    def __setPdvmDate(self,pdvmdt):
        try:
            self.pdvmdatetime = float(int(pdvmdt))
            self.__pdvmDateInDateSplit()
            self.__pdvmdatime(self.year,self.month,self.day,
                            self.hour,self.minute,self.second,self.microsecond)
        except:
            printMessage("error",pdvmObjekt,"PDT_003",["def: setPdvmDate", "Eingabe: " + str(pdvmdt)], self.language)

    def __getPdvmDate(self):
        if self.vChr:
            return self.pdvmdate * -1
        else:
            return self.pdvmdate

    PdvmDate = property(__getPdvmDate,__setPdvmDate)
    
    # --------------------------------------------------------------------
    # PdvmDateT 
    # --------------------------------------------------------------------
    def __setPdvmDateT(self,pdvmdtt):
        try:
            self.__pdvmdatime(pdvmdtt[0],pdvmdtt[1],pdvmdtt[2],0,0,0,0)
        except:
            printMessage("error",pdvmObjekt,"PDT_004",["def: setPdvmDateT", "Eingabe: " + str(pdvmdtt)], self.language)
    
    def __getPdvmDateT(self):
        return self.dd

    PdvmDateT = property(__getPdvmDateT,__setPdvmDateT)
        
    # --------------------------------------------------------------------
    # PdvmTime
    # --------------------------------------------------------------------
    def __setPdvmTime(self,pdvmtt):
        try:
            xx = int(pdvmtt)
            self.pdvmdatetime = float(pdvmtt)-xx  
            self.__pdvmDateInDateSplit()
            self.__pdvmdatime(self.year,self.month,self.day,
                            self.hour,self.minute,self.second,self.microsecond)
        except:
            printMessage("error",pdvmObjekt,"PDT_005",["def: setPdvmTime", "Eingabe: " + str(pdvmtt)], self.language)

    def __getPdvmTime(self):
        return self.pdvmtime

    PdvmTime = property(__getPdvmTime,__setPdvmTime)
    
    # --------------------------------------------------------------------
    # PdvmTimeT 
    # --------------------------------------------------------------------
    def __setPdvmTimeT(self,pdvmttt):
        try:
            self.__pdvmdatime(0,0,0,pdvmttt[0],pdvmttt[1],pdvmttt[2],pdvmttt[3])
        except:
            printMessage("error",pdvmObjekt,"PDT_006",["def: setPdvmTimeT", "Eingabe: " + str(pdvmttt)], self.language)
    
    def __getPdvmTimeT(self):
        return self.dt

    PdvmTimeT = property(__getPdvmTimeT,__setPdvmTimeT)

    # --------------------------------------------------------------------
    # __pdvmdatime(jahr,monat,tag,stunde,minute,sekunde,microsekunde)
    # Eigenschaften der Klasse werden gesetzt, bzw. berechnet
    # --------------------------------------------------------------------
    def __pdvmdatime(self,year=0,month=0,day=0,hour=0,minute=0,second=0,microsecond=0):
        self.year        = year         # Jahr
        self.month       = month        # Monat
        self.day         = day          # Tag im Monat
        self.hour        = hour         # Stunde im Tag
        self.minute      = minute       # Minute in der Stunde
        self.second      = second       # Sekunde in der Minute
        self.microsecond = microsecond  # Microsekunde

        self.pdvmdatetime = self.__convertToPdvmDateTime(year,month,day,hour,minute,second,microsecond)

        self.pdvmtime = float(str(self.pdvmdatetime)[str(self.pdvmdatetime).find("."):])
        self.__svalue()

        return self.pdvmdatetime

    # --------------------------------------------------------------------
    # PdvmdateTime zerlegen
    # --------------------------------------------------------------------
    def __pdvmDateInDateSplit(self):
        ret = self.__splitPdvmDate(self.pdvmdatetime)
        self.year  = ret[0]
        self.month = ret[1]
        self.day   = ret[2]
        self.pdvmtime = float(str(self.pdvmdatetime)[str(self.pdvmdatetime).find("."):])
        cfntmsec    = int(self.pdvmtime * self._tag)     # Microsekunden des Tages
        xistd       = round(cfntmsec / self._stunde,4)         # Stunden mit Rest
        self.hour   = int(xistd)                      # Stunden des Tages
        reststd     = cfntmsec % self._stunde         # Rest Microsekunden
        ximin       = round(reststd / self._minute,4) # Minuten mit Rest
        self.minute = int(ximin)                      # Minuten der Stunde
        restmin     = reststd % self._minute          # Rest Microsekunden
        xisec       = round(restmin / self._sekunde,4)# Sekunden mit Rest
        self.second = int(xisec)                      # Sekunden der Minute
        if self.second==60:                           # Korrektur Ungenauigkeit
            self.second = 0                           #    bei Ursprungswert 0
        restsec     = restmin % self._sekunde         # Rest Microsekunden
        self.microsecond     = int(restsec)           # Microsekunden der Sekunde
        if self.microsecond > 999000:                 # Korrektur Ungenauigkeit
            self.microsecond = 0                      #    bei Ursprungswert 0
            
        self.__svalue()

        return self.dtt

    # --------------------------------------------------------------------
    # Objektwerte
    # --------------------------------------------------------------------
    def __svalue(self):
        # Tuple Datum / Zeiten setzen
        ret = []
        ret.append(self.year)
        ret.append(self.month)
        ret.append(self.day)
        self.dd = tuple(ret)
        ret1 = []
        ret1.append(self.hour)
        ret1.append(self.minute)
        ret1.append(self.second)
        ret1.append(self.microsecond)
        self.dt = tuple(ret1)
        self.dtt = tuple(ret)+tuple(ret1)
        self.period = (self.year * 100) + self.month

        return True

    # --------------------------------------------------------------------
    # Weekday    --- Wochentag ermitteln
    # --------------------------------------------------------------------
    def __getWeekday(self):
        # Wochentag wird auf Basis der Gesamttage ab Beginn des
        # des Kalenders berechnet und inter die Tage im Jahr addiert.
        # Jahr 0 hat Wochentag 5 Samstag, Jahr 1 hat 6 Sonntag, da der
        # Kalender im Jahre 1 mit Sonntag beginnt.  
        # Für das Jahr 0 und die negative Jahre wird dieses einfach logisch
        #    weitergeführt     
        year = self.year                # Jahreszahl
        if self.vChr:   
            year = year * -1          
        x_year = year                   # für spätere Verwendung        
        if year <= 0:                   # für Jahr 0 und kleiner, volle Jahre ohne Korrektur    
            pass
        else:
            year -= 1                   # Anzahl volle Jahre
        yday = self.yday                # Anzahl Tage im Jahr
        sjahr= int(year/4)              # Anzahl grundsätzliche Schaltjahre
        n_sjahr = int(year/100)         # Anzahl doch keine Schaltjahre
        d_jahr = int(year/400)          # Anzahl doch wieder Schaltjahre
        all_years_day = year*365        # Anzahl Tage der Jahre
        all_s_years = sjahr - n_sjahr + d_jahr      # Summe der Schaltjahre
        if x_year < 1:
            year_number = all_years_day + all_s_years - yday
        else:    
            year_number = all_years_day + all_s_years + yday -1
        return year_number%7

    Weekday = property(__getWeekday,)

    # --------------------------------------------------------------------
    # Schaltjahr ermitteln 
    # --------------------------------------------------------------------
    def __lYearFYear(self,year):
        s = 0
        if year != 0:                   # 0 % x immer 0
            r = year % 4                # jedes 4 Jahr --> Schaltjahr
            if r==0:
                r = year % 100          # alle 100 Jahre --> keine Schaltjahr
                if r==0:
                    r = year % 400      # alle 400 Jahre wieder --> Schaltjahr
                    if r==0:
                        s = 1           # Schaltjahr
                    else: 
                        s = 0           # kein Schaltjahr
                else:
                    s = 1               # Schaltjahr
            else:
                s = 0                   # kein Schaltjahr

        return  s                       # Rückgabe Ergebnis

    # --------------------------------------------------------------------
    # Date    --- Datum yyyy-mm-dd ausgeben 
    #           Datumsformate nach DIN 5008:2011-04
    #
    #   auf dieses Format werden wir uns immer beziehen. Die Unterschiede in 
    #   Trennzeichen, besonderer Formate (DEU, ENG, USA) werden demnach nur 
    #   in unterschiedlichen Darstellungsformen (Ausgaben) wiederspiegeln.
    #   Dazu schaffen wir uns Parameter für das Objekt
    #       - Form Land (ohne Angabe - DIN) [self.formCountry] siehe Property
    #       - Trennzeichen (ohne Angabe oder kein Land - DIN) aus formCountry [dateSplitter]
    #       - Position Jahr (ohne Angabe oder kein Land - DIN) aus formCountry [dateYearPos]
    #       - Position Monat (ohne Angabe oder kein Land - DIN) aus formCountry [dateMonthPos]
    #       - Ausgabe Stellen Monat / Tag (ohne Angabe oder kein Land - DIN) aus formCountry [monthDayLen]
    #   mit __setFormCountry als Objektparameter gesetzt.
    #   Hinweis: Erfolgt eine Eingabe mit ainem Minus am Anfang so wird intern self.vChr auf True 
    #   -------- gesetzt. In den Berechungen hat es noch keine Auswirkungen. Datum wird wie positiv
    #            verwaltet. Als PDVM_DateTime erfolgt die Ausgabe und damit ggf. auch die Speicherung negativ.
    # --------------------------------------------------------------------
    def __setDate(self,datein):
        # Initalisierung
        ok    = True
        year  = 0
        month = 0
        day   = 0
        pdate  = {
            'year':year,
            'month':month,
            'day':day
        }
        splitter = '-'
        # Datum mit korrektem Splitter wird einfach zerlegt, egal ob Tag Monat 1 oder zweistellig sind
        # Es sollen ja alle Jahre (auch < 1000) verarbeitet werden können. Vorerst keine Modifikation von
        # 2-stelligen Jahreszahlen.
        # Eingaben ohne Splitter setzt voraus, Tag / Monat immer 2-stellig, Jahreszahl 4 Stellen, wenn 
        # zwei Stellen, dann folgende Modifikationsregel (bis aktuelles Jahr + 5 --> aktuelles Jahrundert //
        # danach Jahrundert - 1)
        # Bei 4 Stellen wird davon ausgegangen, dass das aktuelle Jahr gültig ist
        if datein[0:1]=='-':
            self.vChr = True
            datein = datein[1:]
        else:
            self.vChr = False
        datein = datein.replace('/', '-')
        datein = datein.replace('.', '-')
        if datein.find(splitter) == -1:        # Trennzeichen nicht gefunden
            try:
                int(datein)                             # Prüfung numerischer Wert
            except:
                printMessage("error",pdvmObjekt,"PDT_007",["def: __setDate","Eingabe: " + datein], self.language)
                ok = False

            if ok == True:       # kein Splitter und numerisch
                if len(datein) > 8:                       # für numerischen Wert zu lange
                    printMessage("error",pdvmObjekt,"PDT_008",["def: __setDate","Eingabe: " + datein], self.language)
                    ok = False
                elif (len(datein) == 8                    # mit 4 Stellen Jahr
                        or len(datein) == 6               # mit 2 Stellen Jahr
                        or len(datein) == 4):             # ohne Jahreszahl
                    pdate = self.__calcDateToForm(datein, len(datein))
                else:
                    printMessage("error",pdvmObjekt,"PDT_009",["def: __setDate","Eingabe: " + datein], self.language)
                    ok = False
        else:
            xdate = datein.split(splitter)
            
            for i in range(0, 3):
                if outpos[self.dateYearPos][self.dateMonthPos][i]==0:
                    year = xdate[i]
                if outpos[self.dateYearPos][self.dateMonthPos][i]==1:
                    month = xdate[i]
                if outpos[self.dateYearPos][self.dateMonthPos][i]==2:
                    day = xdate[i]

            pdate = [year,month,day]

            for i in range(1, 3):
                if len(pdate[i])==1:
                    pdate[i] = pdate[i].rjust(2, "0")

        if ok:
            ok = self.__checkDate(pdate[0],pdate[1],pdate[2])

        if ok:
            self.PdvmDateT = (int(pdate[0]),int(pdate[1]),int(pdate[2]))
            return 0        # Return 0k - Datum gesetzt
        else:
            return -1       # Return für falsch - Datum nicht gesetzt

    def __getDate(self):
        ret = ()
        xdate = [str(self.year),str(self.month),str(self.day)]
        for i in range(1, 3):                           # 0 ist Jahr bleibt wie es ist
            if len(xdate[i])<self.monthDayLen:
                    xdate[i] = xdate[i].rjust(2, "0")
            ret = (xdate[outpos[self.dateYearPos][self.dateMonthPos][0]]
                +self.dateSplitter+xdate[outpos[self.dateYearPos][self.dateMonthPos][1]]
                +self.dateSplitter+xdate[outpos[self.dateYearPos][self.dateMonthPos][2]])

        return ret

    Date = property(__getDate,__setDate)
    
    # -------------------------------------------------------------------------------------
    # Datum prüfen
        # ---------------------------------------------------------------------------------
        # Hinweis: Heute muss das Jahr noch positiv sein. Auf Dauer möchte ich hier auch Daten vor 
        # -------- Chr. nach den Regeln des Gregorianischen Kalenders, als negative Zahl verarbeiten.
        #          Daher wird eine Prüfung auf das Jahr weggelassen.
        # ---------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------------
    def __checkDate(self,year,month,day):
        ok = False

        # Check Month
        if int(month) > 0 and int(month) < 13:
            ok = True
        else:
            printMessage("error",pdvmObjekt,"PDT_010",["def: __checkDate","Monat: " + str(month)], self.language)
        
        # Check Day
        # Der Tag wird genau geprüft, dies bedeutet, dass beim Februar das Schaltjahr 
        # geprüft werden muss.
        if ok:
            md = monthdays[int(month)+1][int(self.__lYearFYear(int(year)))]-monthdays[int(month)][int(self.__lYearFYear(int(year)))]
            if int(day)>0 and int(day)<md+1:
                ok = True
            else:
                ok = False
                printMessage("error",pdvmObjekt,"PDT_011",["def: __checkDate", "Tag: " + str(day),"Monat: " + str(month),"Jahr: " + str(year)], self.language)

        return ok

    # --------------------------------------------------------------------
    # Date (ohne Trenner) nach Spezifikation in Jahr / Monat / Tag konvertieren
    # --------------------------------------------------------------------
    def __calcDateToForm(self, datein, dlen):
        year  = 0
        month = 0
        day   = 0

        # Jahr ermitteln
        ayear2 = self.GetAYear2
        ajh2   = self.GetAYearH2
        if dlen == 8:
            year = datein[posYear[dlen][self.dateYearPos][0]:posYear[dlen][self.dateYearPos][1]]
        elif dlen == 6:
            year = datein[posYear[dlen][self.dateYearPos][0]:posYear[dlen][self.dateYearPos][1]]
            if (int(ayear2)+5) < int(year):
                year = str(((int(ajh2) - 1)*100)+int(year))
            else:
                year = str((int(ajh2)*100)+int(year))
        elif dlen == 4:
            year = self.GetAYear
        else:
            # darf hier nie ankommen / Sicherheit
            printMessage("error",pdvmObjekt,"PDT_012",["def: __calcDateToForm","Länge: " + str(dlen)], self.language)

        # Monat ermitteln
        month = datein[posMonth[dlen][self.dateMonthPos][0]:posMonth[dlen][self.dateMonthPos][1]]

        # Tag ermitteln
        day = datein[posDay[dlen][self.dateMonthPos][0]:posDay[dlen][self.dateMonthPos][1]]

        return year, month, day

    # --------------------------------------------------------------------
    # Time
    #
    # Hier werden nur Stunden, Minuten und Sekunden zugelassen. 
    # Der Trenner ist hier : .. ohne Trenner müssen alle Bereiche mit 2 Stellen eingegeben werden.
    # als zusätzlich Trenner werden auch . und , beachtet
    # Die Millisekunden werden immer mit 0 angefügt
    # Bei Landformat USA sind die Angaben von PM und AM zugelassen. Ohne Angabe kann die Stunden-
    #    eingabe auch mit 24 Stunden erfolgen, dieses wird dann intern umgesetzt.
    # --------------------------------------------------------------------
    def __setTime(self,timein):
        hour = 0
        minute = 0
        second = 0
        ok = True
        sok = False
        splitter = ':'
        timein = timein.replace(',',splitter)
        timein = timein.replace('.',splitter) 
        if timein.find(splitter)>0:
            timein = timein + splitter + '0'            # für den Fall, wenn nur ein Splitter
            sok = True                                  # nur pos 0 bis 2 werden übernommen    
        if sok:         # Eingabe mit Splitter
            tis = timein.split(splitter)
            for i in range(0,3):                        # falls ein Bereich leer ist
                if tis[i]=='':
                    tis[i] = 0
            try:
                hour = tis[0]
                minute = tis[1]
                second = tis[2]
            except:
                printMessage("error",pdvmObjekt,"PDT_014",["def: __setTime","Splitwert: " + str(tis)], self.language)
                ok = False
        else:           # Eingabe ohne Splitter
            try:
                int(timein)                             # Prüfung numerischer Wert
            except:
                printMessage("error",pdvmObjekt,"PDT_007",["def: __setTime","Eingabe: " + timein], self.language)
                ok = False
            if ok and len(timein)%2 > 0:                       #falsche Länge nicht durch 2 teilbar
                printMessage("error",pdvmObjekt,"PDT_012",["def: __setTime","Eingabe: " + timein], self.language)
                ok = False
            elif ok and len(timein) > 6:                         # zu lang
                printMessage("error",pdvmObjekt,"PDT_008",["def: __setTime","Eingabe: " + timein], self.language)
                ok = False
            if ok:    
                tin = (timein + '000000')[0:6]
                hour   = tin[0:2]
                minute = tin[2:4]
                second = tin[4:6]

        if ok:
            self.PdvmTimeT = (int(hour),int(minute),int(second),0)
            return 0
        else:
            return -1

    def __getTimeCalc(self):
        if self.formCountry == 'USA':
            if self.hour > 12 and self.hour < 24: 
                hour = self.hour - 12
                pmam = ' PM'
            elif self.hour < 12:
                hour = self.hour
                pmam = ' AM'
            elif self.hour == 12:
                hour = self.hour
                pmam = ' PM'
            elif self.hour == 24:
                hour = self.hour - 12
                pmam = ' AM'
        else:
            hour = "%02i" % self.hour
            pmam = ''
        minute = "%02i" % self.minute
        second = "%02i" % self.second

        return str(hour)+':'+str(minute)+':'+str(second),pmam

    def __getTime(self):        # Ausgabe Stunden, Minuten, Sekunden
        gein = self.__getTimeCalc()
        return gein[0]+gein[1]

    def __getTimeAll(self):     # Ausgabe Stunden, Minuten, Sekunden, Microsekunden
        gein = self.__getTimeCalc()
        return gein[0]+'.'+str(self.microsecond)+gein[1]

    def __getTimeShort(self):   # Ausgabe Stunden, Minuten 
        gein = self.__getTimeCalc()
        return str(gein[0])[0:5]+gein[1]

    Time = property(__getTime,__setTime)
    TimeAll = property(__getTimeAll)
    TimeShort = property(__getTimeShort)
    # --------------------------------------------------------------------
    # LYear    --- Schaltjahr ausgeben   0 kein Schaltjahr / 1 Schaltjahr
    # --------------------------------------------------------------------
    def __getLYear(self):
        return self.__lYearFYear(self.year)

    LYear = property(__getLYear,)

    # --------------------------------------------------------------------
    # YDay    --- Tag im Jahr
    # --------------------------------------------------------------------
    def __getYDay(self):
        return self.yday

    YDay = property(__getYDay,)

    # --------------------------------------------------------------------
    # FormTimeStamp    --- Zeitstempel ausgeben
    # --------------------------------------------------------------------
    def __setFormTimeStamp(self, inaxxo):             # muss ggf. noch ausgebaut werden
        dt = inaxxo.split(' - ')
        self.Date = dt[0]
        da = self.pdvmdatetime
        self.Time = dt[1]
        self.PdvmDateTime = float(da) + float(self.pdvmdatetime)

    def __getFormTimeStamp(self):
        if self.vChr:
            return "-"+self.Date + " - " + self.Time
        else:
            return self.Date + " - " + self.Time

    def __getTimeStamp(self):
        if self.vChr:
            return "-"+self.Date + " - " + self.TimeAll
        else:
            return self.Date + " - " + self.TimeAll

    FormTimeStamp = property(__getFormTimeStamp, __setFormTimeStamp)
    TimeStamp = property(__getTimeStamp)    
    # --------------------------------------------------------------------
    # DecHour    --- Dezimalstunden ausgeben
    # --------------------------------------------------------------------
    def __getDecHour(self):
        return int(round(self.hour/24*100,0))

    DecHour = property(__getDecHour,)

    # --------------------------------------------------------------------
    # DecMin    --- Dezimalminuten ausgeben
    # --------------------------------------------------------------------
    def __getDecMin(self):
        return int(round(self.minute/3*5,0))

    DecMin = property(__getDecMin,)

    # --------------------------------------------------------------------
    # DecSec    --- Dezimalsekunden ausgeben
    # --------------------------------------------------------------------
    def __getDecSec(self):
        return int(round(self.second/3*5,0))

    DecSec = property(__getDecSec)

    # --------------------------------------------------------------------
    # HourDec    --- Stunden dezimal ausgeben
    # --------------------------------------------------------------------
    def __getHourDec(self):
        return (self.hour +(self.DecMin/100)+(self.DecSec/10000) +
               (self.microsecond/10000000000))

    HourDec = property(__getHourDec)

    # --------------------------------------------------------------------
    # MinDec    --- Minuten dezimal ausgeben
    # --------------------------------------------------------------------
    def __getMinDec(self):
        return (self.minute+(self.DecSec/100) +
                (self.microsecond/100000000))

    MinDec = property(__getMinDec)

    # --------------------------------------------------------------------
    # Year    --- Jahr ausgeben
    # --------------------------------------------------------------------
    def __getYear(self):
        return self.year

    Year = property(__getYear,)

    # --------------------------------------------------------------------
    # Month    --- Monat ausgeben
    # --------------------------------------------------------------------
    def __getMonth(self):
        return self.month

    Month = property(__getMonth,)

    # --------------------------------------------------------------------
    #Dday    --- Tag ausgeben
    # --------------------------------------------------------------------
    def __getDay(self):
        return self.day

    Day = property(__getDay,)

    # --------------------------------------------------------------------
    # Hour    --- Stunde ausgeben
    # --------------------------------------------------------------------
    def __getHour(self):
        return self.hour

    Hour = property(__getHour,)

    # --------------------------------------------------------------------
    # Minute    --- Minute ausgeben
    # --------------------------------------------------------------------
    def __getMinute(self):
        return self.minute

    Minute = property(__getMinute,)

    # --------------------------------------------------------------------
    # Second    --- Sekunde ausgeben
    # --------------------------------------------------------------------
    def __getSecond(self):
        return self.second

    Second = property(__getSecond,)

    # --------------------------------------------------------------------
    # Period    --- Periode (JJJJMM) ausgeben (Monat)  [Monatsperiode]
    # --> wird immer positiv ausgegeben
    # --------------------------------------------------------------------
    def __getPeriod(self):
        return self.period

    Period = property(__getPeriod,)

    # --------------------------------------------------------------------
    # FirstDayOfMonth    --- 1. Tag des Monats / Periode
    # --> nur bei positivem Datum korrekt
    # --------------------------------------------------------------------
    def __getFirstDayOfMonth(self):
        year = self.year
        month = self.month
        s = self.LYear
        day = int(monthdays[month][s]+1)
        if month == 0:
            day = 0
        return (year*1000)+day

    FirstDayOfMonth = property(__getFirstDayOfMonth)

    # --------------------------------------------------------------------
    # LastDayOfMonth    --- letzter Tag des Monats
    # --> nur bei positivem Datum korrekt
    # --------------------------------------------------------------------
    # --- A c h t u n g !!  Monat endet erst am Folgetag um 00:00 Uhr
    # --------------------------------------------------------------------
    def __getLastDayOfMonth(self):
        year = self.year
        month = self.month
        s = self.LYear
        day = int(monthdays[month+1][s])
        if month == 0:
            day = 0
        return (year*1000)+day

    LastDayOfMonth = property(__getLastDayOfMonth)

    # --------------------------------------------------------------------
    # FrstDayOfNextMonth    --- 1. Tag des nächsten Monats
    # --> nur bei positivem Datum korrekt
    # --------------------------------------------------------------------
    # --- A c h t u n g !!  Es ist das Ende des Vormonats, 00:00 Uhr
    # --------------------------------------------------------------------
    def __getFirstDayOfNextMonth(self):
        year = self.year
        month = self.month
        if month == 12:
            month = 0
            year += 1
        s = self.__lYearFYear(year)
        day = int(monthdays[month+1][s]+1)
        if month == 0:
            day = 1
        if year == 0:
            day = 0
        return (year*1000)+day

    FirstDayOfNextMonth = property(__getFirstDayOfNextMonth)

    # --------------------------------------------------------------------
    # PdvmDateTimeNow   --- aktueller Tag und Zeit
    # --- Objekt wird auf den aktuellen Tag und die aktuelle Zeit gesetzt
    # --------------------------------------------------------------------
    def PdvmDateTimeNow(self):
        lt = time.localtime(time.time())  # Localtime
        return self.__convertToPdvmDateTime(lt[0],lt[1],lt[2],lt[3],lt[4],
                                            lt[5],lt[6])

    # --------------------------------------------------------------------
    # aktuelles Jahr ermitteln
    # --------------------------------------------------------------------
    def __getAYear(self):
        lt = time.localtime(time.time())  # Localtime
        return lt[0]

    GetAYear = property(__getAYear)

    # --------------------------------------------------------------------
    # aktuelles Jahr ermitteln 2 Stellen
    # --------------------------------------------------------------------
    def __getAYear2(self):
        year = self.GetAYear
        ret = str(year)[2:4]
        return ret

    GetAYear2 = property(__getAYear2)

    # --------------------------------------------------------------------
    # aktuelles Jahrhundert ermitteln 2 Stellen
    # --------------------------------------------------------------------
    def __getAYearH2(self):
        year = self.GetAYear
        ret = str(year)[0:2]
        return ret

    GetAYearH2 = property(__getAYearH2)

    # --------------------------------------------------------------------
    # AddMonthPeriod   --- Monate werden zur Periode addiert
    # --------------------------------------------------------------------
    def AddMonthPeriod(self,val):
        ret = self.__upDown(self.month + val,self.year,12)
        return (ret[1]*100)+ret[0]

    # --------------------------------------------------------------------
    # AddYearPeriod   --- Jahre werden zur Periode addiert
    # --------------------------------------------------------------------
    def AddYearPeriod(self,val):    # Jahr kann auch ins Minus laufen
        e_month = self.month
        e_year = self.year + val
        return (e_year*100)+e_month

    # --------------------------------------------------------------------
    # AddYear   --- Jahre werden zum PdvmDateTime addiert
    # --------------------------------------------------------------------
    def AddYear(self,val):
        return self.AddToPdvmDateTime(val,0,0,0,0,0)
        
    # --------------------------------------------------------------------
    # AddMonth   --- Monate werden zum PdvmDateTime addiert
    # --------------------------------------------------------------------
    def AddMonth(self,val):
        return self.AddToPdvmDateTime(0,val,0,0,0,0)

    # --------------------------------------------------------------------
    # AddDay   --- Tage werden zum PdvmDateTime addiert
    # --------------------------------------------------------------------
    def AddDay(self,val):
        return self.AddToPdvmDateTime(0,0,val,0,0,0)

    # --------------------------------------------------------------------
    # AddHour   --- Stunden werden zum PdvmDateTime addiert
    # --------------------------------------------------------------------
    def AddHour(self,val):
        return self.AddToPdvmDateTime(0,0,0,val,0,0)

    # --------------------------------------------------------------------
    # AddMinute   --- Minuten werden zum PdvmDateTime addiert
    # --------------------------------------------------------------------
    def AddMinute(self,val):
        return self.AddToPdvmDateTime(0,0,0,0,val,0)

    # --------------------------------------------------------------------
    # AddSecond   --- Sekunden werden zum PdvmDateTime addiert
    # --------------------------------------------------------------------
    def AddSecond(self,val):
        return self.AddToPdvmDateTime(0,0,0,0,0,val)

    # --------------------------------------------------------------------
    # AddToPdvmDateTime   --- addiert Zeiten
    # --------------------------------------------------------------------
    def AddToPdvmDateTime(self,a_year=0,a_month=0,a_day=0,a_hour=0,
                         a_minute=0,a_second=0):
        year        = self.year   + a_year
        month       = self.month  + a_month
        day         = self.day    + a_day
        hour        = self.hour   + a_hour
        minute      = self.minute + a_minute
        second      = self.second + a_second
        microsecond  = self.microsecond   # wird nicht addiert
        ck = 0
        if a_second != 0:
            ck += 1
        if ck > 0:    
            res = self.__upDown(second,minute,60)
            second = res[0]
            minute = res[1]
        if a_minute != 0:
            ck += 1
        if ck > 0:    
            res = self.__upDown(minute,hour,60)
            minute = res[0]
            hour = res[1]
        if a_hour != 0:
            ck += 1
        if ck > 0:    
            res = self.__upDown(hour,day,24)
            hour = res[0]
            day = res[1]
        if a_month != 0:
            ck += 1
        if ck > 0:    
            res = self.__upDown(month,year,12)
            month = res[0]
            year = res[1]
        s = self.__lYearFYear(year)            
        yday = int(monthdays[month][s]+day)    
        maxday = (int(monthdays[13][0]),int(monthdays[13][1]))
        myd = maxday[s]
        while int(yday) > myd:
            yday -= myd
            year += 1
            s = self.__lYearFYear(year)            
            myd = maxday[s]
        while int(yday) < 1:
            year -= 1
            s = self.__lYearFYear(year)            
            myd = maxday[s]
            yday += myd
        res = self.__splitPdvmDate((year*1000)+yday)
        year  = res[0]
        month = res[1]
        day   = res[2]
        self.PdvmDateTimeT = (year,month,day,hour,minute,second,microsecond)
        return self.__convertToPdvmDateTime(year,month,day,hour,minute,
                                         second,microsecond)

    # --------------------------------------------------------------------
    # DiffToPdvmDateTime   --- Differenz zu self.PdvmDateTime und Value (PdvmDateTime)
    # --------------------------------------------------------------------
    def DiffToPdvmDateTime(self,val):
        ret = self.__splitPdvmDateTime(val)
        d_year   =  ret[0] - (self.year)
        d_month  =  ret[1] - (self.month)
        d_day    =  ret[2] - (self.day)
        d_hour   =  ret[3] - (self.hour)
        d_minute =  ret[4] - (self.minute)
        d_second =  ret[5] - (self.second)
        return (d_year,d_month,d_day,d_hour,d_minute,d_second) 
        
    # --------------------------------------------------------------------
    # __upDown   --- Para 1 --> auf Max // Para 2 --> Überlauf // Max
    # --------------------------------------------------------------------
    def __upDown(self,s,z,m):
        while s > m:
            s -= m
            z  += 1
        while s < 1:
            s += m
            z  -= 1
        return (s,z)

    # --------------------------------------------------------------------
    # __splitPdvmDate   PdvmDate wird in year,month,day zerlegt
    # --------------------------------------------------------------------
    def __splitPdvmDate(self,pdvmdate):
        if pdvmdate > 1000:
            yday = int(pdvmdate % 1000)               # Tage im Jahr
            year = int((pdvmdate - yday) / 1000)      # Jahr
            s = self.__lYearFYear(year)               # Schaltjahr
            ret = 0
            for i in range(13,-1,-1):
                if int(yday) < monthdays[i][s]+1:
                    pass
                else:
                    if ret==0:
                        ret = i
                        mfndays_e = monthdays[i][s]
                        break
            month  = ret                           # Monat
            day    = int(yday - mfndays_e)         # Tag
        else:
            year  = 0
            month = 0
            day   = 0
        return (year,month,day)

    # --------------------------------------------------------------------
    # __splitPdvmDateTime  PdvmdateTime (Differenz) wird in alle Teile zerlegen
    # --------------------------------------------------------------------
    def __splitPdvmDateTime(self, pdvmdatetime):
        ret = self.__splitPdvmDate(pdvmdatetime)
        year  = ret[0]
        month = ret[1]
        day   = ret[2]
        pdvmtime  = float(str(pdvmdatetime)[str(pdvmdatetime).find("."):])
        cfntmsec  = int(pdvmtime * self._tag)        # Microsekunden des Tages
        xistd     = round(cfntmsec / self._stunde,4) # Stunden mit Rest
        hour      = int(xistd)                       # Stunden des Tages
        reststd   = cfntmsec % self._stunde          # Rest Microsekunden
        ximin     = round(reststd / self._minute,4)  # Minuten mit Rest
        minute    = int(ximin)                       # Minuten der Stunde
        restmin   = reststd % self._minute           # Rest Microsekunden
        xisec     = round(restmin / self._sekunde,4) # Sekunden mit Rest
        second    = int(xisec)                       # Sekunden der Minute
        if self.second==60:                          # Korrektur Ungenauigkeit
            self.second = 0                          #    bei Ursprungswert 0
        restsec   = restmin % self._sekunde          # Rest Microsekunden
        microsecond  = int(restsec)                  # Microsekunden der Sekunde
        if microsecond > 999000:                     # Korrektur Ungenauigkeit
            microsecond = 0                          #    bei Ursprungswert 0
            
        return (year,month,day,hour,minute,second)

    # --------------------------------------------------------------------
    # __convertToPdvmDateTime   --- Einzelzeiten geben PdvmDateTime zurück
    # --------------------------------------------------------------------
    def __convertToPdvmDateTime(self,year,month,day,hour,minute,second,microsecond):
        # calc Tag im Jahr   
        self.yday = self.__calcToDayInYear(year, month, day)

        # PdvmDate setzen
        self.pdvmdate = (year * 1000) + self.yday

        # PdvmDateTime setzen
        # gesamter Zeitwert als Microsekunde
        zeitwert = ((hour * self._stunde) + (minute * self._minute) +
                    (second * self._sekunde) + microsecond)
        # Microsekundenwert auf Tage
        timevalue = zeitwert / self._tag 
      
        pdvmdatetime = timevalue + self.pdvmdate

        return pdvmdatetime

    # --------------------------------------------------------------------
    # FullProperties   --- gibt alle Properties als Wörterbuch zurück
    # ------------------------------------------------------"--------------
    def FullProperties(self):
        fullprop = {
        "PdvmDateTime"        : str(self.PdvmDateTime),
        "PdvmDate"            : str(self.PdvmDate),
        "PdvmTime"            : str(self.PdvmTime),
        "PdvmDateTimeT"       : str(self.PdvmDateTimeT),
        "PdvmDateT"           : str(self.PdvmDateT),
        "PdvmTimeT"           : str(self.PdvmTimeT),
        "Date"                : str(self.Date),
        "Time"                : self.Time,
        "YDay"                : str(self.YDay),
        "Weekday"             : str(self.Weekday),
        "LYear"               : str(self.LYear),
        "Period"              : str(self.Period),
        "FormTimeStamp"       : self.FormTimeStamp,
        "FirstDayOfMonth"     : str(self.FirstDayOfMonth),
        "LastDayOfMonth"      : str(self.LastDayOfMonth),
        "FirstDayOfNextMonth" : str(self.FirstDayOfNextMonth),
        "Year"                : str(self.year),
        "Month"               : str(self.month),
        "Day"                 : str(self.day),
        "Hour"                : str(self.hour),
        "Minute"              : str(self.minute),
        "Second"              : str(self.second),
        "DecHour"             : str(self.DecHour),
        "DecMin"              : str(self.DecMin),
        "DecSec"              : str(self.DecSec),
        "HourDec"             : str(self.HourDec),
        "MinDec"              : str(self.MinDec),
        }

        return fullprop

    # --------------------------------------------------------------------
    # PrintFullProperties   --- gibt alle Properties als Tabelle (Log) zurück
    # --------------------------------------------------------------------
    def PrintFullProperties(self, mod):
        l = '35'
        fullp = self.FullProperties()
        if mod == 1:
            print(multiChar("-",70,1))
            for pro in fullp:
                print(transString (pro, self.proptext, l)+" : "+fullp[pro])
                print('    ['+pro+']')
                print(multiChar("-",70,0))
        else:
            print(transString('FormTimeStamp', self.proptext, l)+" : "+fullp['FormTimeStamp'])

    # --------------------------------------------------------------------
    # errechnet den Tag im Jahr (Industrietag)
    # --------------------------------------------------------------------
    def __calcToDayInYear(self, year, month, day):
        s = self.__lYearFYear(year)
        yday = int(monthdays[month][s]+day) 
        return yday   

    # --------------------------------------------------------------------
    # Übersetzungen und anderes
    # --------------------------------------------------------------------
    # Wochentagname 
    def __weekdayName(self, gwd):
        return transkateone('weekdays',str(gwd), self.language) 

    # Monatsnamen 
    def __transMN(self, tmn):
        return transkateone('monthname',str(tmn-1), self.language)              

    # Translation Ja/Nein  1/0
    def __transYN(self, tjn):
        return transkateone('transYN',str(tjn), self.language)    



#  Ende der Klasse
# --------------------------------------------------------------------
# hilfreiche Funktionalitäten
#=====================================================================

# --------------------------------------------------------------------
# PDVM Datum / Zeit formatiert ausgeben
# --------------------------------------------------------------------
def getFormTimeStamp(tidt,fC='DIN'):
    ti = Pdvm_DateTime(fC)
    ti.PdvmDateTime = tidt
    return ti.FormTimeStamp
    
def getFormDate(tidt,fC='DIN'):
    ti = Pdvm_DateTime(fC)
    ti.PdvmDateTime = tidt
    return ti.Date

def getFormTime(tidt,fC='DIN'):
    ti = Pdvm_DateTime(fC)
    ti.PdvmDateTime = tidt
    return ti.Time

def getDateTimeNow():
    return Pdvm_DateTime().PdvmDateTimeNow() 

def getAYear():
    ti = Pdvm_DateTime()
    ti.PdvmDateTime = getDateTimeNow()
    return ti.year

# --------------------------------------------------------------------
# übersetzte String 'pdvmstr' mit Kategorie 'pdvmkat' auf die Länge 'pdvml' 
# --------------------------------------------------------------------
def transString (pdvmstr, pdvmkat, pdvml):
    vstr = pdvmkat[pdvmstr]
    ret =('{:<'+pdvml+'}').format(vstr)
    return ret

# --------------------------------------------------------------------
# übersetzte String 'pdvmstr' mit Kategorie 'pdvmkat' auf die Länge 'pdvml' 
# direkt aus dem Wörterbuch mit der Sprache 'lanq'
# --------------------------------------------------------------------
def transStringOne (lang, pdvmkat, pdvmstr, pdvml):
    vstr = transkateone(pdvmkat, pdvmstr, lang)
    ret =('{:<'+pdvml+'}').format(vstr)
    return ret

# --------------------------------------------------------------------
# String auf die Länge pdvml konvertieren
# --------------------------------------------------------------------
def stringToLength (pdvmstr, pdvml):
    ret =('{:<'+pdvml+'}').format(pdvmstr)
    return ret




# --------------------------------------------------------------
# für Test / Ausgabe und Berechnung - müssen direkt eingebunden sein
# --------------------------------------------------------------

def tests_print (a, test_list, testname='ohne Parameter', 
        fixValue=0, variValue=0, show_datail = [], show_mod=0):
    p_print(show_detail[6],  "--- get "+variValue)    
    exec('test_list[testname] = [testname, '+fixValue+', '+ variValue+']')
    if show_detail[3] : print(test_list[testname])
    if show_detail[6] == 1 : a.PrintFullProperties(show_detail[show_mod])
    p_print(show_detail[6],  multiChar("-",70,1))
    return a

def test_out (a, test_pro, test_in):
    p_print(show_detail[6],  "--- set " +test_pro+ " = " + str(test_in))
    exec("a."+test_pro+" = " + test_in)
    return a

# --------------------------------------------------------------
# --------------------------------------------------------------

# Hauptprogramm - Testumgebung
# --------------------------------------------------------------
if __name__=='__main__':
    # --------------------------------------------------------------
    import os                                  # Für Testbereich
    from pdvm_util import lockedWritten, multiChar, p_print, t_p_t  
    # das Wörterbuch mit den einzelnen Testelementen wurde ausgelagert
    import pdvm_datetime_test
    tests = pdvm_datetime_test.testtabelle()
    # --------------------------------------------------------------
    try:                    # Console wir leer gemacht
        os.system('CLS')    # for Windows
    except:
        os.system('CLEAR')  # for Unix

    a = Pdvm_DateTime()                                 # Objekt wird initialisiert / Standardsprache

    linel = 70                  # Länge der Linien im Log
    print(multiChar("=",linel,1))
    print(lockedWritten(transkateone('general','OutTestProt', a.language)))
    print(multiChar("=",linel,2))
    blank = "----> "            # einrücken verschiedener Ausgaben
    test_list = {}

    a = Pdvm_DateTime()         # Objekt für default Test
    a.PdvmDateTime = a.PdvmDateTimeNow()
    akt_year = str(a.Year)      # muss auf dem aktuellen Jahr stehen
    tag_4monC = (               # Tage 4 Monate vom aktuellen Monat zurück [Test0230]
        (122,122),(122,122),(120,121),(120,121),(119,120),(122,122),
        (121,121),(122,122),(122,122),(122,122),(122,122),(121,121)
    )
    tag_4mon = int(tag_4monC[a.Month][a.LYear])


    # Einstellungen zur Log-Ausgabe
    show_detail = [
        0,                      # (0) Details nach init / nur wenn 6 = 0
        0,                      # (1) Details bei dem Setzen / nur wenn 6 = 0
        0,                      # (2) Details bei den Additionen / nur wenn 6 = 0
        0,                      # (3) print Testdaten im Log
        0,                      # (4) print Testdaten am Ende
        0,                      # (5) Detail Date/Time / nur wenn 6 = 0
        0,                      # (6) Ergebnis im Log ausgeben / Fehlermeldungen kommen immer
    ]


    # Start des eigentlichen Testes
    # --------------------------------------------------------------------------------

    if show_detail[0] == 1:                             # ggf. Ausgabe der Eigenschaften
        p_print(show_detail[6], a.FullProperties() )
    if show_detail[6] == 1 : a.PrintFullProperties(show_detail[0])
    p_print(show_detail[6], multiChar("-",linel,0))

    p_print(show_detail[6],  a.FormCountry)
    a.FormCountry = 'deu'
    p_print(show_detail[6],  a.FormCountry)
    a.FormCountry = 'USA '
    p_print(show_detail[6],  a.FormCountry)
    a.FormCountry = ' eng '
    p_print(show_detail[6],  a.FormCountry)
    a.FormCountry = ' enl '                         # Fehlermeldung FormCountry = DIN
    p_print(show_detail[6],  a.FormCountry)

    fC = input('\n'+ transkateone('general', 'countryFDate', a.language) +': ')   # Eingabe FormCountry für den Test
    a = Pdvm_DateTime(fC)                           #   korrekter Test muss mit allen FormCountry
    la = a.language                                 # Sprache in kurze Veriable
    p_print(show_detail[6],  a.formCountry)         #   ok sein.

    # --------------------------------------------------------------------------------
    # Tests aus den Wörterbuch-Definitionen (pdvm_datetime_test,py)
    tfc = ('DIN', 'DEU', 'ENG', 'USA')
    for sts in tests:
        for tfcEle in tfc:
            if a.formCountry == tfcEle:
                erg = tests[sts][tfcEle]
                break
        a = test_out(a, tests[sts]['tset'], tests[sts]['tins'])
        tests_print(a, test_list, sts, erg, tests[sts]['tget'], show_detail, tests[sts]['tlog'])

    # Ende Test aus den Wörterbuch-Definitionen
    # --------------------------------------------------------------------------------

    # Besonderer Test in der Addition - direkt erstellt
    # --------------------------------------------------------------------------------
    p_print(show_detail[6],  "--- AddToPdvmDateTime  (1,2,3,4,5,6) ")
    p_print(show_detail[6],   t_p_t(la, 'Year')+', '+ t_p_t(la, 'Month')+', '+ t_p_t(la, 'Days')+', '+
        t_p_t(la, 'Hours')+', '+ t_p_t(la, 'Minutes')+', '+ t_p_t(la, 'Seconds'))
    p_print(show_detail[6],  multiChar("-",linel,0))
    b = Pdvm_DateTime(a.formCountry)
    b.PdvmDateTimeT = a.PdvmDateTimeT 
    res = a.AddToPdvmDateTime(1,2,3,4,5,6)
    l = '8'
    p_print(show_detail[6],  transStringOne (la, 'general', 'addition', l)+": " + str(res))
    p_print(show_detail[6],  transStringOne (la, 'general', 'blank', l)+"  " + str(a.FormTimeStamp))
    p_print(show_detail[6],  transStringOne (la, 'general', 'origin', l)+": "+ str(b.PdvmDateTime))
    p_print(show_detail[6],  transStringOne (la, 'general', 'blank', l)+"  "  + str(b.FormTimeStamp) + "\n")

    t1 = b.PdvmDateTime
    p_print(show_detail[6],  "--- DiffToPdvmDateTime  von der Addition ")
    p_print(show_detail[6],   t_p_t(la, 'Year')+', '+ t_p_t(la, 'Month')+', '+ t_p_t(la, 'Days')+', '+
        t_p_t(la, 'Hours')+', '+ t_p_t(la, 'Minutes')+', '+ t_p_t(la, 'Seconds'))
    p_print(show_detail[6], multiChar("-",linel,0))
    res1 = b.DiffToPdvmDateTime(res)
    p_print(show_detail[6],  str(res1))
    # Differenz wird wieder addiert. Ergebnist muss gleich dem Eingang sein
    res2 = b.AddToPdvmDateTime(res1[0], res1[1], res1[2], res1[3], res1[4], res1[5])
    l = '32'
    p_print(show_detail[6],  transStringOne (la, 'general', 'ResAfterDiffAddition', l)+": " + str(res2))
    p_print(show_detail[6],  transStringOne (la, 'general', 'blank', l)+"  " + str(b.FormTimeStamp))

    p_print(show_detail[6],  multiChar("-",linel,2))

    p_print(show_detail[6],  "--- AddToPdvmDateTime  (-1,-2,-3,-4,-5,-6) ")
    p_print(show_detail[6],   t_p_t(la, 'Year')+', '+ t_p_t(la, 'Month')+', '+ t_p_t(la, 'Days')+', '+
        t_p_t(la, 'Hours')+', '+ t_p_t(la, 'Minutes')+', '+ t_p_t(la, 'Seconds'))
    p_print(show_detail[6], multiChar("-",linel,0))
    b = Pdvm_DateTime(a.formCountry)
    b.PdvmDateTimeT = a.PdvmDateTimeT 
    res = a.AddToPdvmDateTime(-1,-2,-3,-4,-5,-6)
    l = '8'
    p_print(show_detail[6],  transStringOne (la, 'general', 'addition', l)+": " + str(res))
    p_print(show_detail[6],  transStringOne (la, 'general', 'blank', l)+"  " + str(a.FormTimeStamp))
    p_print(show_detail[6],  transStringOne (la, 'general', 'origin', l)+": "+ str(b.PdvmDateTime))
    p_print(show_detail[6],  transStringOne (la, 'general', 'blank', l)+"  "  + str(b.FormTimeStamp) + "\n")

    p_print(show_detail[6],  "--- DiffToPdvmDateTime  von der Addition ")
    p_print(show_detail[6],   t_p_t(la, 'Year')+', '+ t_p_t(la, 'Month')+', '+ t_p_t(la, 'Days')+', '+
        t_p_t(la, 'Hours')+', '+ t_p_t(la, 'Minutes')+', '+ t_p_t(la, 'Seconds'))
    p_print(show_detail[6],  multiChar("-",linel,0))
    res1 = b.DiffToPdvmDateTime(res)
    p_print(show_detail[6],  str(res1))
    # Differenz wird wieder addiert. Ergebnist muss gleich dem Eingang sein
    res2 = b.AddToPdvmDateTime(res1[0], res1[1], res1[2], res1[3], res1[4], res1[5])
    l = '32'
    p_print(show_detail[6],  transStringOne (la, 'general', 'ResAfterDiffAddition', l)+": " + str(res2))
    p_print(show_detail[6],  transStringOne (la, 'general', 'blank', l)+"  " + str(b.FormTimeStamp))

    # mit dem tests_print wird das Ergebnis in die allgemeine Prüfung einbezogen
    tests_print(a, test_list, 'Test_1010', 't1', 'res2', show_detail, 2)

    # Testet die Formatierte Ausgabe eines PdvmDateTime - wird immer ausgegeben
    print("\nT e s t  -- Form PdvmDateTime --> TimeStamp")
    print(multiChar("=",linel,0))
    l = '30'
    a.PdvmDateTime = getDateTimeNow()
    print(transStringOne (la, 'proptext', 'FormCountry', l)+" : "+ a.FormCountry)
    print(transStringOne (la, 'proptext', 'PdvmDateTimeNow', l)+" : "+ str(a.PdvmDateTime))
    print(transStringOne (la, 'proptext', 'FormTimeStamp', l)+" : "+ str(a.FormTimeStamp))
    print(transStringOne (la, 'proptext', 'TimeStamp', l)+" : "+ str(a.TimeStamp))
    print(transStringOne (la, 'proptext', 'Date', l)+" : "+ str(a.Date))
    print(transStringOne (la, 'proptext', 'Time', l)+" : "+ str(a.Time ))
    print(transStringOne (la, 'proptext', 'TimeShort', l)+" : "+ str(a.TimeShort))


    # Testausgabe - erfolgt nach den Einstellungen
    if show_detail[4] == 1:
        print(multiChar("=",linel,1))
        print(lockedWritten(transkateone('general','testEdition', a.language)))
        print(multiChar("=",linel,0))
        for test_d in test_list:
            print(test_list[test_d])
    
    print(multiChar("=",linel,1))
    print(lockedWritten(transkateone('general','testResult', a.language)))
    print(multiChar("=",linel,0))
    er = 0
    for test_d in test_list:
        if test_list[test_d][1] != test_list[test_d][2]:
            print(transkateone('general','diffIn', a.language)+" " + test_d + " -- " + 
                str(test_list[test_d][1]) + " -- " + str(test_list[test_d][2]))
            er += 1
    if er > 0:
        print(str(er) + " "+ transkateone('general','diffExist', a.language))
    else:
        print(transkateone('general','noDiff', a.language)+" - Test OK")

    a = Pdvm_DateTime('DEU')
    a.Date = '-17.10.5'
    print(a.Weekday)
    print(transkateone('weekdays', str(a.Weekday), a.language))
    print(a.PdvmDateTime)
    print(a.TimeStamp)
