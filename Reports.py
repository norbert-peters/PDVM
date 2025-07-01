
def rep1():
    return '''Die Editionswissenschaft erlebt nicht zuletzt wegen einer 
        erfolgreichen Kombination von traditionellen Arbeitsweisen 
        mit Methoden der Digital Humanities einen regelrechten Hype. 
        Digitale Methoden drängen sich besonders an den Stellen auf, 
        wo sie eine Überwindung der Beschränkungen des analogen Drucks versprechen. 
        Zugleich zeichnet sich ab, dass mit einem Wechsel zu digitalen Editionsformen 
        nicht nur neue Werkzeuge genutzt werden, sondern dass sich prinzipielle 
        strukturelle Änderungen ergeben: so können analoge Editionen angereichert 
        werden oder Editionen können als Hybrid durch eine gleichwertige digitale und 
        analoge Version repräsentiert werden. Editoren werden angesichts dieser neuen
        Möglichkeiten vor neue Herausforderungen gestellt. Gleiches gilt für Infrastrukturen, 
        die die Produkte der Editionswissenschaft publizieren und langfristig 
        verfügbar machen sollen. Grundlegende Fragen der Qualitätsmessung 
        und -bewertung, der Arbeitsorganisation, Vernetzung und Distribution 
        müssen bei der digitalen Editionswissenschaft anders bzw. neu gestellt 
        und bewertet werden. Die vom Forschungsverbund Marbach Weimar Wolfenbüttel 
        veranstaltete Tagung “Digitale Metamorphose: Digital Humanities und Editionswissenschaft” 
        betrachtete diese neuen Möglichkeiten kritisch und ging dabei auch der Frage nach, 
        welche Grenzen und Gefahren es jenseits der offensichtlichen Vorteile für 
        die Editionswissenschaft gibt.'''

"""tokenize_text() soll folgende Operationen beinhalten:
        Entfernung von Interpunktionszeichen
        Lowercasing aller Großbuchstaben
        Tokenisierung der Textdaten anhand von Whitespaces"""

def tokenize_text(pd_text):
    pd_text_b = pd_text.replace(".", "")
    pd_text_b = pd_text_b.replace(",", "")
    pd_text_b = pd_text_b.replace(":", "")
    pd_text_b = pd_text_b.replace("!", "")
    pd_text_b = pd_text_b.replace("\n", "")
 
    pd_text_i = pd_text_b.split(" ")
    pd_text_i1 = [satz for satz in pd_text_i if satz]  # leere Sätze entfernen

    print("Funktion tokenize zu Ende!")
    return pd_text_i1 



"""segment_text() soll die tokenisierten Textdaten zu Segmenten in folgender Art weiterverarbeiten:
    Segmente sollten nicht länger als 10 Wörter sein
    Der Text soll am Ende zeilenweise (\n) als zusammenhängende Zeichenkette ausgegeben werden."""

def segment_text(pd_text):
    pd_text = pd_text.replace("\n", "")
    pd_text_i = pd_text.split(" ")
    pd_text_i = [satz for satz in pd_text_i if satz]  # leere Sätze entfernen
    pd_out = ""
    pd_out_e = ""
    pd_start = 0
    pd_ende = 10

    for y in range(0, 20):
        for i in range(pd_start, pd_ende):
            pd_out = pd_out + pd_text_i[i] + " "

        pd_start = pd_ende + 1
        pd_ende = pd_ende + 11
        if pd_ende >= len(pd_text_i):
            pd_ende = len(pd_text_i)
        pd_out_e = pd_out_e + pd_out + "\n"  
        pd_out = ""  



    print("Funktion tokenize zu Ende!")
    return pd_out_e


pd_ret = segment_text(rep1())
print(f"{pd_ret}")