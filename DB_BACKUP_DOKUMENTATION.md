# PostgreSQL Backup-Dokumentation (lokal, ohne Docker Pull)

## Ziel
Diese Dokumentation beschreibt die eingerichtete Backup-Lösung für lokale PostgreSQL-Datenbanken auf diesem Rechner.

- Backup-Zielordner: D:\PDVM-System_DB_Backup
- Ausführung: lokales PostgreSQL (Port 5432)
- Pull von Container-Images ist nicht erforderlich

## Hintergrund
Docker Pulls schlagen in dieser Umgebung mit EOF fehl. Daher wurde eine robuste lokale Backup-Strategie mit pg_dump umgesetzt.

## Eingerichtete Skripte
1) Backup aller lokalen Datenbanken
- C:\Users\norbe\OneDrive\Dokumente\MyApplication\scripts\backup_postgres_local_all.ps1

Funktion:
- Liest alle nicht-Template-Datenbanken
- Erstellt je Datenbank eine .dump-Datei
- Schreibt nach D:\PDVM-System_DB_Backup
- Löscht alte Dumps automatisch (Standard: älter als 14 Tage)

2) Passwort sicher speichern (DPAPI)
- C:\Users\norbe\OneDrive\Dokumente\MyApplication\scripts\set_pg_backup_secret.ps1

Funktion:
- Speichert DB-Passwort verschlüsselt per Windows DPAPI
- Secret-Datei ist an den aktuellen Benutzer gebunden
- Setzt eingeschränkte Datei-ACL auf den aktuellen Benutzer

3) Geplanten Task registrieren
- C:\Users\norbe\OneDrive\Dokumente\MyApplication\scripts\register_daily_db_backup_task.ps1

Funktion:
- Erstellt/aktualisiert Task: PDVM_Daily_Postgres_Backup
- Tägliche Ausführung um 02:00
- Kein Klartext-Passwort in der Task-Aktion

## Secret-Datei
- Pfad: C:\Users\norbe\OneDrive\Dokumente\MyApplication\scripts\secrets\pg_backup_password.txt
- Inhalt: DPAPI-verschlüsselter String
- Wichtiger Hinweis: Nur derselbe Windows-Benutzer kann das Secret entschlüsseln

## Aktuelle Task-Konfiguration
- Taskname: PDVM_Daily_Postgres_Backup
- Zeitplan: täglich 02:00
- Modus: Nur interaktiv
- Letztes Ergebnis erfolgreich: 0

## Nutzung
### Passwort initial/neu setzen
PowerShell im Projektordner:

powershell -ExecutionPolicy Bypass -File .\scripts\set_pg_backup_secret.ps1 -Password "<DEIN_PASSWORT>"

### Manuelles Backup starten

powershell -ExecutionPolicy Bypass -File .\scripts\backup_postgres_local_all.ps1

Optionale Parameter:
- -DbHost (Standard 127.0.0.1)
- -Port (Standard 5432)
- -User (Standard postgres)
- -BackupRoot (Standard D:\PDVM-System_DB_Backup)
- -KeepDays (Standard 14)
- -PasswordFile (Standard auf Secret-Datei)

### Task neu registrieren/anpassen

powershell -ExecutionPolicy Bypass -File .\scripts\register_daily_db_backup_task.ps1 -TaskName "PDVM_Daily_Postgres_Backup" -Time "02:00"

### Task manuell testen

schtasks /Run /TN PDVM_Daily_Postgres_Backup

Status prüfen:

schtasks /Query /TN PDVM_Daily_Postgres_Backup /V /FO LIST

## Restore
Beispiel für Restore in eine Zieldatenbank:

"C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" -h 127.0.0.1 -p 5432 -U postgres -d <ziel_db> "D:\PDVM-System_DB_Backup\<datei>.dump"

Vorher ggf. leere Zieldatenbank anlegen.

## Verifikation
Backups kontrollieren:

Get-ChildItem D:\PDVM-System_DB_Backup -File | Sort-Object LastWriteTime -Descending | Select-Object -First 20 Name,Length,LastWriteTime

Erwartung:
- Neue Dateien mit aktuellem Zeitstempel
- Dateigröße > 0

## Troubleshooting
1) Fehler: Datenbank existiert nicht
- Ursache: Falscher DB-Name
- Lösung: DB-Liste prüfen:

"C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -p 5432 -U postgres -d postgres -t -c "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;"

2) Fehler: Authentifizierung fehlgeschlagen
- Ursache: Passwort stimmt nicht
- Lösung: Secret neu setzen mit set_pg_backup_secret.ps1

3) Task läuft nicht wie erwartet
- Letztes Ergebnis in Task Scheduler prüfen
- Manuell über schtasks /Run testen
- Script-Ausgabe direkt in PowerShell prüfen

## Sicherheitshinweise
- Kein Klartext-Passwort im Task-Kommando
- Secret ist lokal verschlüsselt und benutzergebunden
- Beim Wechsel des Windows-Benutzers Secret neu erzeugen
- Zugriff auf Backup-Ordner regelmäßig prüfen (NTFS-Rechte)
