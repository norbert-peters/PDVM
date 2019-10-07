# pdvm_util.py
# ------------------------------------------------------------------
# 01.07.2018 Norbert Peters
# ------------------------------------------------------------------
""" Eine Sammlung von viel verwendeter Funktionen
--- getNewId --> liefert eine neue UUID/GUID im Format string zurück
--- getStaticId --> liefert eine statische UUID/GUID aus einem Zeichen zurück
--- __checkHexValue --> prüft ob Zeichen für einen Hex String zugelassen sind
"""
# ------------------------------------------------------------------
import uuid                                 # import Modul uuid

def getNewId():                             # Definition der Funktion
    return str(uuid.uuid4())                # neue UUID/GUID

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
        r = "Eingabezeichen "+str(zahl)+" ist nicht zugelassen!"
        return r

def __checkHexValue(zeich):                 # Prüfung zugelassener Zeichen
    zeichen = [0,1,2,3,4,5,6,7,8,9,'a','b','c','d','e','f']
    if zeich in zeichen:
        return True
    else:
        return False
   
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