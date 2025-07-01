import tkinter as tk

def aktionSF():
    pd_init = " "
    pd_mehr = 30
    pd_aus = pd_init*pd_mehr
    label3 = tk.Label(root, text=pd_aus, bg="lightblue")
    label3.grid(row=3, column=1, sticky="w")
    label3 = tk.Label(root, text=str(eingabefeld_wert.get()), bg="lightblue")
    label3.grid(row=3, column=1, sticky="w")
    ausgabe_2()

def ausgabe():
    aktuell_ausgewaehlt = ausgewaehlt.get()
    label2 = tk.Label(root, text=aktuell_ausgewaehlt, bg="lightgreen")
    label2.grid(row=2, column=1, sticky="W")

def ausgabe_2():
    for i, var in enumerate(variablen):
        label4 = tk.Label(root, 
                          text=f"CheckButton {i+1}: {'ausgewählt          ' if var.get() else 'nicht ausgewählt'}", 
                          bg="lightgreen").grid(row=10+i, column=1, sticky="W")


pd_path = "C:/Users/norbe/OneDrive/Dokumente/Versuche/"

# Liste für CheckButtons und ihre Variablen
checkbuttons = []
variablen = []


root = tk.Tk()              # Fenster initalisieren

# Textausgabe erzeugen
label0 = tk.Label(root, text = " Meine Welt ", 
                  fg="#00ff00",
                  bg="orange",
                  font=('times', 25, 'bold', 'italic'),
                  height=1, width=20, anchor="s")

# inGUI Elemente einbetten
label0.grid(row=0, column=1)

label1 = tk.Label(root, text="Hallo Welt", bg="orange")
label1.grid(row=1, column=0)


# Grafik einbetten
bild1 = tk.PhotoImage(file=pd_path + "biene.png")
label99 = tk.Label(root, image=bild1).grid(row=4, column=2)

# einzeiliges Eingabefeld
eingabefeld_wert=tk.StringVar()
eingabefeld=tk.Entry(root,
                     textvariable=eingabefeld_wert,
                     show="*").grid(row=5,column=0,sticky="W")
eingabefeld_wert.set("bitte eingeben:")

anrede = ["Frau    ", "Herr    ", "Diverse"]

ausgewaehlt = tk.StringVar()
ausgewaehlt.set("Frau    ")

# RadioButton über Liste
i = 6
for einzelwert in anrede:
    radiob = tk.Radiobutton(root, 
                            text=einzelwert, 
                            value=einzelwert, 
                            variable=ausgewaehlt,
                            command=ausgabe)
    radiob.grid(row=i, column=0,sticky="w")
    i = i+1

aktuell_ausgewaehlt = ausgewaehlt.get()

# CheckButtons erstellen und zur Liste hinzufügen
gruppehobby = tk.LabelFrame(root, text="Ihre Hobbies?", fg="#00ff00")
gruppehobby.grid(row=9, column=1,sticky="w")

texte = ["Sport treiben", "lesen", "Filme schauen"]
x = 1
for text in texte:
    var = tk.BooleanVar()
    checkbutton = tk.Checkbutton(gruppehobby, text=text, variable=var)
    checkbutton.grid(sticky="w")
    x=x+1
    checkbuttons.append(checkbutton)
    variablen.append(var)

schaltf1 = tk.Button(root, 
                     text="Aktion durchführen",
                     command=aktionSF,
                     cursor='hand2',
                     highlightthickness="10").grid(row=16, column=2,sticky="e") 

schaltf2 = tk.Button(root, 
                     text="beenden",
                     command=root.destroy,
                     cursor='tcross',
                     highlightthickness="10").grid(row=16, column=0,sticky="w") 


root.mainloop()             # Hauptschleife
