'''Hier werden die DefaultWerte für den Personalstamm eingestellt. Das Ab-Datum 1.0 wird bei
   einer Neuanlage durch das betreffende Ab-Datum überschrieben'''

def pers_base_data():
    # Daten für den Personalstamm
    return  {
        'PersDaten': {
            'Personalnummer': {
                1.0: 'ABC999',
            },
            'Name': {
                1.0: None,
            },
            'Vorname': {
                1.0: None,
            },
            'Titel': {
                1.0: None,
            },
            'Vorsatzwort': {
                1.0: None,
            },
            'Anrede': {
                1.0: None,
            },
            'Geschlecht': {
                1.0: None,
            },
            'Familienstand': {
                1.0: None,
            },
            'Geburtsdatum': {
                1.0: '199001.0'
            },
            'Telefon': {
                1.0: '+49 4711'
            }
        },
        'Anschrift_Person': {
            'Strasse': {
                1.0: 'Musterstraße'
            },
            'Hausnummer': {
                1.0: '1'
            },
            'Zusatz': {
                1.0: None
            },
            'Postleitzahl': {
                1.0: '12345'
            },
            'Ort': {
                1.0: 'Musterstadt'
            },
            'Teilort': {
                1.0: None,
            },
            'Anmerkung': {
                1.0: None
            }
        },
        'Sozialversicherung': {
            'Versicherungsnummer': {
                1.0: '1234567890',
            }
        },
        'Steuer': {
            'Steuernummer': {
                1.0: '111222333',
            }
        }
    }


def menu_base_date():
    #Date für die Menüs
    return {
        'PD_commands': None,
        'PD_grund': None,
        'PD_menu': None,
        'PD_zusatz': {
            'PD_z_Grund': None,
            'PD_z_Menu': None
        }
    }
