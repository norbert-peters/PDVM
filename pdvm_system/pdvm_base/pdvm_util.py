# pdvm_util.py
# --------------------------------------------------------------------------
# 01.07.2018 Norbert Peters
# 08.10.2019 erweitert - Norbert Peters
# --------------------------------------------------------------------------
""" Eine Sammlung von viel verwendeter Funktionen
--- getNewId        --> liefert eine neue UUID/GUID im Format string zurück
--- getStaticId     --> liefert eine statische UUID/GUID aus einem Zeichen zurück
--- lockedWritten   --> String gesperrt zurückgeben
--- multiChar       --> gibt ein Zeichen (string) mehrfach aus
--- p_print         --> gibt Test aus, wenn show_detail den Wert 1 hat
--- printMessage    --> gibt eine Meldungen im Log aus - sprachbezogen
--- stringToLength  --> String auf die Länge pdvml konvertieren
--- transString     --> übersetzte String 'pdvmstr' mit Kategorie 'pdvmkat' auf die Länge 'pdvml'
--- transStringOne  -->  übersetzte String 'pdvmstr' mit Kategorie 'pdvmkat' auf die Länge 'pdvml' 
                        direkt aus dem Wörterbuch mit der Sprache 'lang'
--- t_p_t           --> übersetzt das Wort in der angebenen Sprache aus Kategorie 'proptext'
--- __checkHexValue --> prüft ob Zeichen für einen Hex String zugelassen sind
"""
# --------------------------------------------------------------------------
import uuid                                             # import Modul uuid
from pdvm_base.pdvm_langtext import transkateone, transkate       # Für Übersetzung Texte
from django.conf import settings                        # Standardeinstellungen immer aus den Settings

try:
    st_language = settings.LANGUAGE_CODE                # verwendete Standardsprache
except:
    st_language = 'en-us'                               # für Test

# --------------------------------------------------------------------------
# liefert eine neue UUID/GUID im Format string zurück
# --------------------------------------------------------------------------
def getNewId():                             # Definition der Funktion
    return str(uuid.uuid4())                # neue UUID/GUID

# --------------------------------------------------------------------------
# liefert eine statische UUID/GUID aus einem Zeichen zurück
# --------------------------------------------------------------------------
def getStaticId(zahl):                      # Definition der Funktion
    if __checkHexValue(zahl):               # nur zugelassene Zeichen verarbeiten
        t=""
        z = 8
        for i in range(36):                 # statik UUID/GUID aus zahl
            if i == z:
                if z < 23:
                    z += 5
                t+="-"
            else:
                t+=str(zahl)
        return t
    else:
        printMessage('error', 'pdvm_util.py', 'PDU_001',aon=str(zahl))
        return getStaticId(0)               # wird als Standard zurückgegeben - Format sicher stellen

# --------------------------------------------------------------------
# gibt eine Meldungen im Log aus - sprachbezogen
# --------------------------------------------------------------------
# !! bei Änderungen bitte in pdvm_langtext nachziehen !!
# --------------------------------------------------------------------
def printMessage(typ,mod,num,aon=' ',lang=st_language):
    la = 70             # Breite der Ausgabe
    li = '10'           # Breite der 1. Spalte

    # Berechnung und Ausgbe der Headline
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
# String gesperrt zurückgeben
# --------------------------------------------------------------------
def lockedWritten(word):
    ret = ''
    for b in word:
        ret = ret+b+' '
    return ret 


# --------------------------------------------------------------------
# gibt ein Zeichen (string) mehrfach aus 
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
# --------------------------------------------------------------------
def transString (pdvmstr, pdvmkat, pdvml):
    vstr = pdvmkat[pdvmstr]
    ret =('{:<'+pdvml+'}').format(vstr)
    return ret

# --------------------------------------------------------------------
# übersetzte String 'pdvmstr' mit Kategorie 'pdvmkat' auf die Länge 'pdvml' 
# direkt aus dem Wörterbuch mit der Sprache 'lang'
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

# --------------------------------------------------------------------
# gibt Test aus, wenn show_detail den Wert 1 hat
# --------------------------------------------------------------------
def p_print(show_detail, prt):
    if show_detail == 1 : print(prt)

# --------------------------------------------------------------------
# übersetzt das Wort in der angebenen Sprache aus Kategorie 'proptext'
# --------------------------------------------------------------------
def t_p_t(lang, word):
    return transkateone('proptext', word, lang)



# --------------------------------------------------------------------
# prüft ob Zeichen für einen Hex String zugelassen sind
# --------------------------------------------------------------------
def __checkHexValue(zeich):                 # Prüfung zugelassener Zeichen
    zeichen = [0,1,2,3,4,5,6,7,8,9,'a','b','c','d','e','f']
    if zeich in zeichen:
        return True
    else:
        return False
   
# --------------------------------------------------------------------
# Hier werden Tests gesteuert ausgegeben - muss direkt eingebunden sein.
# --------------------------------------------------------------------
# def tests_print (a, test_list, testname='ohne Parameter', 
#         fixValue=0, variValue=0, show_datail = [], show_mod=0):
#     p_print(show_detail[6],  "--- get "+variValue)    
#     exec('test_list[testname] = [testname, '+fixValue+', '+ variValue+']')
#     if show_detail[3] : print(test_list[testname])
#     if show_detail[6] == 1 : a.PrintFullProperties(show_detail[show_mod])
#     p_print(show_detail[6],  multiChar("-",70,1))
#     return a

# --------------------------------------------------------------------
# Führt den Vergleich von Tests aus - muss direkt eingebunden sein
# --------------------------------------------------------------------
#def test_out (a, test_pro, test_in):
#    p_print(show_detail[6],  "--- set " +test_pro+ " = " + str(test_in))
#    exec("a."+test_pro+" = " + test_in)
#    return a





# ------------------------------------------------------------------
# Hauptprogramm - Testumgebung
# ------------------------------------------------------------------
if __name__=='__main__':                    
    import os                               # Für Testbereich

    try:                                    # Console wir leer gemacht
        os.system('CLS')                    # for Windows
    except:
        os.system('CLEAR')                  # for Unix
                                            # Test der Funktionen, wenn
    # Test der Funktion getNewId()          # die Funktionsbibliothek
    b=getNewId()                            # direkt aufgerufen wird
    print("T e s t  -- getNewId() -- Funktion öffentlich")
    print("=============================================")
    print("Neue UUID/GUID: "+b)
    print("Neue UUID/GUID: "+getNewId())

    # Test __checkHexValue
    print("\nT e s t  -- __checkHexValue() -- Funktion privat")
    print("================================================")
    print("Zeichen 0 "+str(__checkHexValue(0)))
    print("Zeichen 9 "+str(__checkHexValue(9)))
    print("Zeichen a "+str(__checkHexValue('a')))
    print("Zeichen f "+str(__checkHexValue('f')))
    print("Zeichen g "+str(__checkHexValue('g')))
    print("Zeichen z "+str(__checkHexValue('z')))
   
    # Test der Funktion staticId(x)  (x = 0-9 oder a-f)
    # dieses sind die ggf. zugelassenen statischen Ids
    print("\nT e s t  -- staticId() -- Funktion öffentlich")
    print("=============================================")
    for i in range(10):
        print("Statische UUID: "+getStaticId(i))
    zeichen = ['a','b','c','d','e','f']
    for i in zeichen:
        print("Statische UUID: "+getStaticId(i))
    # Fehlerprüfung Test
    print("gibt es dieses? "+getStaticId('x'))
    print("gibt es dieses? "+getStaticId('12'))
    print("gibt es dieses? "+getStaticId('aa'))
    print("gibt es dieses? "+getStaticId('b1'))

