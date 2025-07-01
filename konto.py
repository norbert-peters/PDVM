class Konto:
    """ unsere kleines Bankprogramm zum Verwalten Konten/Geld """
    __geldbestand = 0

    def __init__(self, kontonummer, kontostand=0):
        self.__kontonummer = kontonummer
        self.__kontostand  = kontostand

    def geld_abheben(self, betrag):
        print(self.__kontonummer," Geld wird abgehoben:", betrag)
        self.__kontostand -= betrag
        Konto.__geldbestand -= betrag

    def geld_einzahlen(self, betrag):
        print(self.__kontonummer," Geld wird eingezahlt:", betrag)
        self.__kontostand += betrag
        Konto.__geldbestand += betrag

    def kontostand_anzeigen(self):
        print(self.__kontonummer," aktueller Kontostand: ", self.__kontostand)
        print(self.__kontonummer," aktueller Geldbestand der Bank: ", Konto.__geldbestand, "\n")

    def kontostand_aktuell(self):
        return self.__kontostand 

    def kto_nr(self):
        return self.__kontonummer   

class Pluskonto(Konto):
    """ ein Konto, dass nicht überzogen werden kann """

    def __init__(self, kontonummer, kontostand=0):
        """ Initalisieren über Eltern-Klasse """
        super().__init__(kontonummer, kontostand=0)

    def geld_abheben(self, betrag):
        print(self.kto_nr()," Geld soll vom Pluskonto abgehoben werden:", betrag)
        print(self.kto_nr()," Maximal verfügbar ist gerade:", self.kontostand_aktuell())

        konto_akt = self.kontostand_aktuell() - betrag
        
        if konto_akt >= 0:
            print(self.kto_nr()," Auszahlen von Pluskonto: ", betrag)
            super().geld_abheben(betrag)            
        else:
            print(self.kto_nr()," Sorry, Konto kann nicht überzogen werden!")
            if konto_akt + betrag > 0:
                super().geld_abheben(konto_akt + betrag)  
                print(self.kto_nr()," Es konnte nur der Betrag von ", konto_akt + betrag, " abgehoben werden." )


plus1 = Pluskonto("1223329")
plus1.geld_einzahlen(200)
plus1.geld_abheben(300)
plus1.geld_abheben(50)
