import tkinter as tk
from tkinter import ttk, messagebox

# Beispielhafte Metadaten für die Suchliste
suchlisten_metadaten = {
    "personen": {
        "titel": "Personensuche",
        "spalten": [
            {
                "name": "Familienname",
                "feld": "PersDaten.Name",       # Pfad innerhalb der Datensatzstruktur
                "sortierbar": True,
                "suchbar": True,
                "typ": "text"
            },
            {
                "name": "Vorname",
                "feld": "PersDaten.Vorname",
                "sortierbar": True,
                "suchbar": True,
                "typ": "text"
            },
            {
                "name": "Geburtsdatum",
                "feld": "PersDaten.Geburtsdatum",
                "sortierbar": True,
                "suchbar": True,
                "typ": "datum"
            },
            {
                "name": "Anrede",
                "feld": "PersDaten.Anrede",
                "sortierbar": False,
                "suchbar": True,
                "typ": "dropdown"
            }
        ]
    }
}

# Simulierte Personendaten (in der echten Anwendung werden diese aus der DB geladen)
# Jeder Eintrag stellt einen Personendatensatz dar. Hier verwenden wir die gleichen Feldpfade wie in den Metadaten.
personendaten = [
    {
        "GUID": "guid-001",
        "PersDaten": {
            "Name": "Mustermann",
            "Vorname": "Max",
            "Geburtsdatum": "1967-08-01",
            "Anrede": "m"  # Intern: z. B. "m"
        }
    },
    {
        "GUID": "guid-002",
        "PersDaten": {
            "Name": "Musterfrau",
            "Vorname": "Anna",
            "Geburtsdatum": "1975-04-15",
            "Anrede": "w"
        }
    },
    {
        "GUID": "guid-003",
        "PersDaten": {
            "Name": "Beispiel",
            "Vorname": "Peter",
            "Geburtsdatum": "1980-10-30",
            "Anrede": "d"  # z. B. "d" für "Herr oder Frau"
        }
    }
]

# Für die Dropdown-Übersetzung simulieren wir eine einfache Datenstruktur.
# Beispiel: Für "Anrede" wird der interne Schlüssel in den angezeigten Text übersetzt.
dropdown_translations = {
    "anrede": {
        "m": {"de": "Herr", "en": "Mr"},
        "w": {"de": "Frau", "en": "Ms"},
        "d": {"de": "Herr oder Frau", "en": "Mr or Ms"}
    }
}

def get_translation(section, key, language):
    """
    Gibt für einen gegebenen Bereich und Schlüssel die Übersetzung zurück.
    """
    section_data = dropdown_translations.get(section, {})
    option = section_data.get(key)
    if option:
        return option.get(language, key)
    return key

# Funktion zur Suche in den Personendaten (simuliert)
def suche_personen(filter_dict, sortierung=None, limit=50):
    """
    Filtert die simulierten Personendaten anhand von Filterkriterien aus filter_dict.
    filter_dict hat den Aufbau:
      { "PersDaten.Name": "Must", "PersDaten.Vorname": "Max", ... }
    """
    ergebnisse = []
    for person in personendaten:
        passt = True
        for feldpfad, suchtext in filter_dict.items():
            # Teile den Pfad (z. B. "PersDaten.Name")
            try:
                gruppe, feld = feldpfad.split(".")
            except ValueError:
                continue
            wert = person.get(gruppe, {}).get(feld, "")
            if suchtext.lower() not in str(wert).lower():
                passt = False
                break
        if passt:
            # Wähle nur die in den Metadaten definierten Spalten aus
            ergebnis = {"GUID": person.get("GUID")}
            for spalte in suchlisten_metadaten["personen"]["spalten"]:
                pfad = spalte["feld"]
                gruppe, feld = pfad.split(".")
                wert = person.get(gruppe, {}).get(feld, "")
                if spalte["typ"] == "dropdown":
                    wert = get_translation("anrede", wert, "de")
                ergebnis[spalte["name"]] = wert
            ergebnisse.append(ergebnis)
        if len(ergebnisse) >= limit:
            break
    if sortierung:
        ergebnisse.sort(key=lambda x: x.get(sortierung))
    return ergebnisse

# Suchliste-Widget (als Beispiel)
class SuchlisteFrame(ttk.Frame):
    def __init__(self, parent, metadaten, *args, **kwargs):
        """
        Dieses Widget zeigt eine Suchmaske und eine Ergebnis-Tabelle basierend auf den übergebenen Metadaten.
        """
        super().__init__(parent, *args, **kwargs)
        self.metadaten = metadaten["personen"]
        self.filter_vars = {}  # Für jede Spalte ein StringVar für den Filter
        
        # Erstelle einen Suchbereich (Suchfelder pro Spalte)
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        for idx, spalte in enumerate(self.metadaten["spalten"]):
            lbl = ttk.Label(filter_frame, text=spalte["name"], font=("Helvetica", 10, "bold"))
            lbl.grid(row=0, column=idx, padx=5, pady=2)
            var = tk.StringVar()
            entry = ttk.Entry(filter_frame, textvariable=var, width=15)
            entry.grid(row=1, column=idx, padx=5, pady=2)
            self.filter_vars[spalte["feld"]] = var
        
        suche_btn = ttk.Button(filter_frame, text="Suchen", command=self.suchen)
        suche_btn.grid(row=1, column=len(self.metadaten["spalten"]), padx=5, pady=2)
        
        # Erstelle den Treeview für Ergebnisse
        self.tree = ttk.Treeview(self, columns=[s["name"] for s in self.metadaten["spalten"]], show="headings")
        for spalte in self.metadaten["spalten"]:
            self.tree.heading(spalte["name"], text=spalte["name"])
            self.tree.column(spalte["name"], width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Beispiel-Label, um die Anzahl der gefundenen Datensätze anzuzeigen
        self.info_label = ttk.Label(self, text="Keine Ergebnisse", font=("Helvetica", 10))
        self.info_label.pack(padx=5, pady=5)
    
    def suchen(self):
        # Erstelle das Filter-Dictionary
        filter_dict = {}
        for feldpfad, var in self.filter_vars.items():
            text = var.get().strip()
            if text:
                filter_dict[feldpfad] = text
        
        ergebnisse = suche_personen(filter_dict)
        self.zeige_ergebnisse(ergebnisse)
    
    def zeige_ergebnisse(self, ergebnisse):
        # Lösche bestehende Einträge
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Füge neue Einträge hinzu
        for datensatz in ergebnisse:
            values = [datensatz.get(spalte["name"], "") for spalte in self.metadaten["spalten"]]
            self.tree.insert("", "end", values=values)
        self.info_label.config(text=f"Ergebnisse: {len(ergebnisse)} Datensätze")

# Hauptprogramm (zum Testen)
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Suchliste Beispiel")
    root.geometry("800x400")
    
    suchliste = SuchlisteFrame(root, suchlisten_metadaten)
    suchliste.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    root.mainloop()
