import tkinter as tk
from tkinter import ttk

class PdvmDropdown(ttk.Frame):
    def __init__(self, parent, config, current_language="de", stichtag=1001.0, *args, **kwargs):
        """
        Erzeugt ein Dropdown-Widget mit Unterstützung für Mehrsprachigkeit und Historie.
        
        Konfigurationsbeispiel:
        {
            "gruppe": "anrede",
            "name": "Anrede",
            "historical": false,
            "werte": [
                {"key": "mr", "de": "Herr", "en": "Mr", "fr": "Monsieur", "abdatum": "1001.0"},
                {"key": "ms", "de": "Frau", "en": "Ms", "fr": "Madame", "abdatum": "1001.0"}
            ]
        }
        
        Bei historischen Dropdowns werden nur die Optionen angezeigt, deren abdatum kleiner oder gleich dem aktuellen stichtag ist.
        """
        super().__init__(parent, *args, **kwargs)
        self.config_data = config
        self.current_language = current_language
        self.stichtag = float(stichtag)
        self.historical = self.config_data.get("historical", False)
        self.options = []  # Liste der gültigen Optionen (als dict)
        self.display_options = []  # Liste der anzuzeigenden Werte (z.B. in der aktuellen Sprache)
        self.key_to_display = {}   # Mapping: key -> anzuzeigender Wert
        self.display_to_key = {}   # Mapping: angezeigter Wert -> key

        # Variable für die Auswahl
        self.selected_val = tk.StringVar()
        
        # Erstelle die Combobox
        self.combobox = ttk.Combobox(self, textvariable=self.selected_val, state="readonly")
        self.combobox.pack(fill=tk.X, padx=5, pady=5)

        # Initialer Ladevorgang der Optionen basierend auf dem Stichtag
        self.refresh_options(self.stichtag)
        
    def refresh_options(self, stichtag):
        """
        Aktualisiert die Dropdown-Optionen basierend auf dem aktuellen stichtag.
        Für historische Dropdowns werden nur Einträge berücksichtigt, deren abdatum <= stichtag.
        """
        self.stichtag = float(stichtag)
        alle_werte = self.config_data.get("werte", [])
        valid_options = []
        
        # Filtere Optionen für historische Dropdowns
        if self.historical:
            for option in alle_werte:
                try:
                    abdatum = float(option.get("abdatum", "1001.0"))
                except ValueError:
                    abdatum = 1001.0
                if abdatum <= self.stichtag:
                    valid_options.append(option)
            # Sortiere nach abdatum (optional, je nach Logik)
            valid_options.sort(key=lambda opt: float(opt.get("abdatum", "1001.0")))
        else:
            valid_options = alle_werte.copy()
        
        self.options = valid_options
        self.display_options = []
        self.key_to_display.clear()
        self.display_to_key.clear()
        # Fülle die anzuzeigenden Werte in der aktuellen Sprache
        for option in self.options:
            # Wenn für die gewünschte Sprache ein Eintrag existiert, sonst nutze den key
            display_val = option.get(self.current_language, option.get("key"))
            self.display_options.append(display_val)
            self.key_to_display[option.get("key")] = display_val
            self.display_to_key[display_val] = option.get("key")
        
        # Setze die Optionen in der Combobox
        self.combobox['values'] = self.display_options
        if self.display_options:
            self.selected_val.set(self.display_options[0])
        else:
            self.selected_val.set("")
            
    def get_selected_key(self):
        """
        Gibt den Schlüssel der aktuell ausgewählten Option zurück.
        """
        sel = self.selected_val.get()
        return self.display_to_key.get(sel, None)

# Beispielhafte Nutzung:
if __name__ == "__main__":
    root = tk.Tk()
    root.title("PdvmDropdown Beispiel")

    # Beispiel-Konfiguration für ein Dropdown
    dropdown_config = {
        "gruppe": "anrede",
        "name": "Anrede",
        "historical": False,  # Für statische Dropdowns, abdatum wird hier 1001.0 verwendet
        "werte": [
            {"key": "mr", "de": "Herr", "en": "Mr", "fr": "Monsieur", "abdatum": "1001.0"},
            {"key": "ms", "de": "Frau", "en": "Ms", "fr": "Madame", "abdatum": "1001.0"}
        ]
    }
    
    pd_dropdown = PdvmDropdown(root, dropdown_config, current_language="fr", stichtag=2025059.0)
    pd_dropdown.pack(fill=tk.X, padx=10, pady=10)
    
    def show_sel():
        key = pd_dropdown.get_selected_key()
        print("Ausgewählter Schlüssel:", key)
    
    btn = ttk.Button(root, text="Zeige Auswahl", command=show_sel)
    btn.pack(padx=10, pady=10)
    
    root.mainloop()
