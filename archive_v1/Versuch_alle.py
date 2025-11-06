from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import os

#d = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()

#with open("wordcloud-beispieltext.txt") as f:
#    text = f.read()

text = 'Python Kurs: mit Python programmieren lernen für Anfänger und Fortgeschrittene Dieses Python Tutorial entsteht im Rahmen von Uni-Kursen und kann hier kostenlos genutzt werden. Python ist eine für Anfänger und Einsteiger sehr gut geeignete Programmiersprache, die später auch den Fortgeschrittenen und Profis alles bietet, was man sich beim Programmieren wünscht. Der Kurs ist eine Einführung und bietet einen guten Einstieg. Es wird aktuelles Wissen vermittelt - daher schreiben wir unseren Python-Code mit der aktuellen Python-Version 3. einfach Python lernen über das Programmieren von Spielen Damit Python programmieren lernen noch mehr Spaß macht, werden wir im Kurs anhand verschiedener Spiele die Anwendung von Python kennen lernen und unser Wissen als Programmierer aufbauen. Die Grundlagen werden direkt umgesetzt in bekannte Spiele wie:'

nichtinteressant = "und von Der das den wir ist die auf im"
liste_der_unerwuenschten_woerter = nichtinteressant.split()

STOPWORDS.update(liste_der_unerwuenschten_woerter)
wordcloud = WordCloud(background_color="white",width=1920, height=1080).generate(text)

plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.show()