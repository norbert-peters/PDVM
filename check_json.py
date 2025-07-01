import json

json_string = '''{"Anwendungen":{"MeineApps":"5ca6674e-b9ce-4581-9756-64e742883f80","Application":{"Menu":"3424b00f-bb4d-4759-9689-e9e08249117b","Frames":null,"MainApp":null},"Personalwesen":{"Menues":null,"Frames":null,"Daten":null},"Finanzwesen":{"Menues":null,"Frames":null,"Daten":null},"Benutzerdaten":{"Menu":"e1e77039-d1b5-46ff-b12b-cced0ae0da7c","Frames":null}},"Benutzer":{"Anrede":"Herr","Name":"Peters","Vorname":"Norbert",}}'''

try:
    json.loads(json_string)
    print("✅ JSON ist gültig!")
except json.JSONDecodeError as e:
    print(f"❌ Fehler im JSON: {e}")
