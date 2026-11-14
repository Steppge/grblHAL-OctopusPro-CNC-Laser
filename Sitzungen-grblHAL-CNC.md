# Gruppe „grblHAL / CNC“ – Übersicht der Sitzungen

Stand: 14.11.2026, ohne die PC-Deck-Sitzungen. Erstellt aus den Sitzungsverläufen, den Notizen und der Git-Historie.
Die Sitzungen 1 bis 4 sind seit dem 12.11. archiviert, weitergearbeitet wird in Sitzung 5.

## Die Maschine und die Projekte

| Teil | Ordner | Repo / Branch |
|---|---|---|
| Octopus-Firmware (grblHAL, BTT Octopus Pro, F446) | `F:\VisualCode\STM32F4xx-joy` | Fork `Steppge/grblHAL-OctopusPro-CNC-Laser`, Branch `octopus-pro-joy` (Remote `fork`; `origin` = grblHAL upstream) |
| Display-Plugin + ESP32-Display (S3/TS35 und P4 9") | `F:\VisualCode\grblHAL-Plugin-Display` | `Steppge/grblHAL-Plugin-Display`, Submodul `display` |
| Gamepad-Plugin + D1-Mini-Empfänger | `grblHAL-Plugin-Gamepad` | Submodul `gamepad` |
| Octopus-Bridge (ESP32-S3 an der Maschine) | `F:\VisualCode\Octopus-Bridge` | `Steppge/grblHAL-Octopus-Bridge` (öffentlich seit 13.11.) |
| Marlin (alte Firmware, nur noch gepflegt) | `F:\VisualCode\Marlin-neu` | Fork `Steppge/Marlin-OctopusPro-CNC-Laser`, Branch `laser-config` |

Maschine: Laser/CNC, Arbeitsbereich ca. 287 × 232 mm, X/Y 4500 mm/min bei 500 mm/s², Z 1500 mm/min, TMC5160 über SPI, Laser an FAN0. Details in `Maschineneinstellungen.md`.

---

## 1. grblHAL Octopus Pro: Display, Gamepad, Repo (fork)
Hauptsitzung seit Anfang Oktober.

**Erledigt**
- Den grblHAL-Treiber an das Octopus Pro angepasst: eigenes `my_machine.h`/`my_machine_map.h`, Lüfter für die Steuerung an FAN2, Hard Limits strikt, YModem-Upload auf SD, Upload-Skript `tools/upload_firmware.py`.
- Upstream-PR grblHAL/STM32F4xx#307 (HSI-Umschaltung beim Start) am 11.10. ohne Änderungen gemergt. Der Fork bleibt verbunden.
- Joystick-Plugin, danach das Gamepad-Plugin (PS4 über Bluetooth): Joggen, Tasten, Leuchtleiste je Zustand, Rumble. Version 1.3: Home, X0Y0 und Z0 nur mit Jog-Freigabe.
- Display 1.0 auf ESP32-S3 + MKS TS35 (LVGL, Stil „B3 Electric“): Job-Karte, Zoom, STOP mit Halten und anschließendem Abbruch, Z-Balken, Weboberfläche, OTA, LightBurn über WLAN.
- Umstieg auf das CrowPanel 9" ESP32-P4 (1024 × 600), Layout Variante A, gemeinsamer Code in `esp32common/`, Gehäuse.
- TMC5160 über SPI (24.10.), Motortest nach Gehör und Bewegungs-Show in `tools/`.
- Einfrier-Suche gelöst (08.11.): USART1 mit 921600 Baud hat beim SD-Zugriff den Kern blockiert. Jetzt läuft der Gamepad-Link mit 230400. Watchdog (IWDG 2 s) und SD-Timeouts sind geblieben.
- Seitenleiste in Gruppen sortiert.

**Letzte Commits (Octopus):** `6e5cbee` Gamepad-Link 230400, Watchdog, SD-Timeouts · `ab0e016` Display-Submodul: Karte auf Core 0.

## 2. Octopus zu Display WLAN-Brücke
Funkdisplay und Bridge, außerdem die P4-Display-Firmware.

**Erledigt**
- Octopus-Bridge (ESP32-S3 N16R8, COM19): Phase 1 über USB-Kabel zum P4 (2 × CDC mit eigenen 64-Byte-Endpoints), Phase 2 über das eigene versteckte Maschinen-WLAN (AP, TCP 5000 für den Link, UDP 5001 für das Gamepad, Koppeln per USB). Mit gestecktem USB-Kabel ist das WLAN aus.
- D1 Mini (Gamepad-Empfänger) am P4 über J7 (GPIO2/3).
- P4 1.2 und 1.3: Firmware-Dialog, Update über SD-Karte, Uhr, Akkuspannung, Dimmen im CNC-Modus, Drehgeber EC11 (IO50/51/5) als Feed-Override.
- Stromversorgung über Akku: IP5306 an J10, 6 × 18650 parallel (ca. 12,9 Ah). Ein Entladelauf mit 488 min ist in die Akkutabelle eingeflossen.
- Uhrzeit: Nach dem Start holt das Display die Zeit per NTP aus dem Heimnetz, dann wechselt es ins Maschinennetz (`4afc169`).
- Akku-Schwellen (11.11.): 100 % beim Entladen bis 4,15 V (`c1baa54`). Beim Laden 100 % ab 4,20 V, Grün ab 4,21 V (`7f3ae87`). Firmware ist auf COM9 geflasht.

**Offen**
- Die Schwellen oben am vollen Akku prüfen (Sprung auf 100 % und auf Grün).

## 3. Nebensitzungen von 2.
Firmware-Stand am Octopus geprüft (08.11.): grblHAL 1.1f.20261008, Treiber 261006, Plugins Watchdog 1.00, Trinamic 0.33, Gamepad 1.3, Display-Link 1.1, SD-Karte 1.29. Wunsch für das Display: Akkuanzeige im Ruhebild mit Farbwechsel, wenn der Akku voll ist. Umgesetzt wurde das über die Akku-Schwellen in Sitzung 2.

## 4. Lightburn Maschineneinstellung
**Erledigt**
- `Maschineneinstellungen.md` angelegt und mit `$$` abgeglichen.
- X-Strom `$140=1600` mA, Test mit 4500 mm/min und 500 mm/s² ohne Schrittverlust.
- Fliesen-Test mit schwarzer Folie: 66 % bei 3000 mm/min (Alternative 54 % bei 2250 mm/min), Intervall 0,1 mm, Overscan 3–4 mm bei 3000 mm/min.
- Mandala als Bild im Schwellwert-Modus statt als Vektor, deshalb ist kein Linientest nötig.

- Nullpunkt hinten rechts, in LightBurn Ursprung oben rechts (per Jog-Test bestätigt, siehe `Maschineneinstellungen.md`).

**Offen**
- Mitlesen über die Weboberfläche des Displays während eines Jobs wurde angeboten, aber nicht umgesetzt.

## 5. Claude.md review (diese Sitzung, 11.–14.11.)
**Erledigt**
- Diese Übersicht erstellt, die Sitzungen 1 bis 4 archiviert.
- Big-Deck: Kacheln am P4 verschieben (halten, ziehen, `MOVE`), Deck-FW 40.
- P4-Display für Nachbauer: `esp32p4/src/display_config.h` mit `BIGDECK` (Standard 0), `CLOCK`, `ENCODER`, `BATTERY`,
  `GAMEPAD` und den J7-Pins; eigene Werte in `my_display_config.h` (nicht im Repo, bei mir `BIGDECK 1`).
- Konsolenbefehl `shot` und `esp32p4/tools/shot.py`: Bildschirmbilder über die Konsole; fünf Bilder in der README.
- README des Display-Plugins: Abschnitt CrowPanel 9" ESP32-P4 (Teile, Bridge, Einstellungen, Flashen, Gehäuse).
- PC-Taste über der Vollbild-Karte ausgeblendet; Lizenzkopf des Display-Plugins korrigiert.
- Octopus-Bridge veröffentlicht (ohne `wifitest`/`p4usbtest`, Heim-WLAN-Name aus der Historie entfernt).
- Gamepad 1.3 und alle Display-Commits gepusht, Marlin-Fork auf `bugfix-2.1.x` gebracht (ein Konflikt in den Octopus-Pins).
- grblHAL-Sync vom 12.11. eingebunden, Submodule nachgezogen: Octopus läuft mit grblHAL 1.1f.20261107,
  Treiber 261104, SD-Karte 1.30. Lasertest ok.
- Der P4 hängt zurzeit an COM30 (CH340K), nicht an COM9.
- Knopf-Dateien (`knopf50`) im Display-Plugin eingecheckt; Maschineneinstellungen und diese Übersicht im Octopus-Repo.
- PC-Deck-Doku-Sitzung informiert: `BIGDECK` ist standardmäßig 0, `MOVE` läuft auf dem Big-Deck, Port COM30.
- 14.11.: Bild des P4 war nach etwa 10 min seitlich verschoben. Ursache: Unterlauf der Bildausgabe aus dem PSRAM
  (`lcd.dsi: ... underrun happens`). Behoben in `2835a79`: Zeichenstreifen im internen RAM, Pixeltakt 46 statt
  51 MHz, nach einem Unterlauf automatisch neu ausrichten (Panel-Reset wie beim Start, Bild bleibt, ca. 0,2 s dunkel).
  Konsole: `resync`, `status` zeigt Unterläufe und Neuausrichtungen.
- Upstream-Stand geprüft (14.11.): nur SNTP, Modbus RTU, FatFs R0.15 im SD-Plugin; nichts übernommen.
- 14.11.: Uhr im gedimmten Bild mit eigener 120-px-Schrift statt 2,5-fach vergrößerter 48-px-Schrift
  (`esp32p4/tools/clockfont.py`, `font_clock_120.c`, Montserrat unter OFL) – `84ed152`.
- 14.11.: Code-Durchsicht des P4. Hauptfund: `ui_update()` (10/s) hat im Stillstand rund 1,1 Mio. Pixel/s neu
  gezeichnet, weil `show()` und Farb-Setter auch ohne Änderung neu zeichnen ließen. Jetzt etwa 1 000 Pixel/s;
  die USB-Task wartet ohne Daten 2–4 ms und prüft TCP alle 50 ms – `9727cee`. `status` zeigt „redrawn px/s“.
  Im Big-Deck-Layout 6 × 4 werden die Icons nicht gezoomt (erst ab 3 Zeilen).
- 14.11.: Maschinen-Ansicht vor dem Homing zeigt die Vorschau absichtlich nicht (so gewollt), dafür der gelbe
  Hinweis „Home first to see the job in the machine area“ – `982c2f3`.
- 14.11.: Hauptbildschirm: Positionskachel kleiner, Jog-Kachel größer. Tippen auf die Jog-Kachel öffnet „Move“,
  Tippen auf die Position öffnet das neue Fenster „Go to“: Ziel je Achse (nur eingetippte Achsen fahren),
  Workpiece (G54) oder Machine, Reihenfolge Z Y X / Z X Y / X Y Z / Y X Z / Z XY / XY Z / XYZ, Eilgang mit OK
  nur im Idle. Bei Machine bekommt Z automatisch ein Minus (0 = oben) – `3db6e10`.

---

## Offene Punkte gesamt
1. Akku-Schwellen am vollen Akku prüfen (Display P4).
2. Beobachten, ob das P4-Bild gerade bleibt (seit der Durchsicht kaum noch Zeichenlast); bei einem echten
   Unterlauf muss die automatische Neuausrichtung greifen (bisher nur von Hand mit `resync` getestet).
   Kontrolle mit `status` auf COM30: Unterläufe und „redrawn px/s“.
   Falls das Big-Deck auf 3 oder weniger Zeilen umgestellt wird: Icons beim Empfang vorab vergrößern.
3. Nicht eingecheckt im Octopus-Repo: `firmware.bin`, `tools/laser_test.*`, `tools/motor_test_saved.json`.
4. Geplant, noch nicht gebaut:
   - VFD mit 0–10 V an FAN3 als zweite PWM-Spindel, Enable an FAN4 (pausiert seit 08.11.).
     Der neue grblHAL-Stand (20261107) unterstützt geklonte PWM-Spindeln besser.
   - LightBurn über WLAN durch die Bridge (USART3), vorerst bleibt LightBurn an USB.
   - Kamera für LightBurn und das Display.
   - `display_config.h` für das S3-Display (`DISPLAY_TYPE` für MKS TS35 / BTT TFT35).

## Wichtige Ports
| Gerät | Port |
|---|---|
| Octopus (USB) | COM3 |
| P4-Display (CH340K, Konsole/Flash) | COM30 (früher COM9) |
| D1 Mini (Gamepad) | COM10 |
| Octopus-Bridge S3 (CH343) | COM19 |
