# Gruppe „grblHAL / CNC“ – Übersicht der Sitzungen

Stand: 11.11.2026, ohne die PC-Deck-Sitzungen. Erstellt aus den Sitzungsverläufen, den Notizen und der Git-Historie.

## Die Maschine und die Projekte

| Teil | Ordner | Repo / Branch |
|---|---|---|
| Octopus-Firmware (grblHAL, BTT Octopus Pro, F446) | `F:\VisualCode\STM32F4xx-joy` | Fork `Steppge/grblHAL-OctopusPro-CNC-Laser`, Branch `octopus-pro-joy` (Remote `fork`; `origin` = grblHAL upstream) |
| Display-Plugin + ESP32-Display (S3/TS35 und P4 9") | `F:\VisualCode\grblHAL-Plugin-Display` | `Steppge/grblHAL-Plugin-Display`, Submodul `display` |
| Gamepad-Plugin + D1-Mini-Empfänger | `grblHAL-Plugin-Gamepad` | Submodul `gamepad` |
| Octopus-Bridge (ESP32-S3 an der Maschine) | `F:\VisualCode\Octopus-Bridge` | eigenes lokales Repo |

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
- Commits sind nicht gepusht.

## 3. Nebensitzungen von 2.
Firmware-Stand am Octopus geprüft (08.11.): grblHAL 1.1f.20261008, Treiber 261006, Plugins Watchdog 1.00, Trinamic 0.33, Gamepad 1.3, Display-Link 1.1, SD-Karte 1.29. Wunsch für das Display: Akkuanzeige im Ruhebild mit Farbwechsel, wenn der Akku voll ist. Umgesetzt wurde das über die Akku-Schwellen in Sitzung 2.

## 4. Lightburn Maschineneinstellung
**Erledigt**
- `Maschineneinstellungen.md` angelegt und mit `$$` abgeglichen.
- X-Strom `$140=1600` mA, Test mit 4500 mm/min und 500 mm/s² ohne Schrittverlust.
- Fliesen-Test mit schwarzer Folie: 66 % bei 3000 mm/min (Alternative 54 % bei 2250 mm/min), Intervall 0,1 mm, Overscan 3–4 mm bei 3000 mm/min.
- Mandala als Bild im Schwellwert-Modus statt als Vektor, deshalb ist kein Linientest nötig.

**Offen**
- Mitlesen über die Weboberfläche des Displays während eines Jobs wurde angeboten, aber nicht umgesetzt.
- Die Nullpunkt-Ecke der Maschine ist noch unbekannt.

## 5. Claude.md review (diese Sitzung)
Sitzung in die Gruppe grblHAL / CNC einsortiert und diese Übersicht erstellt.

---

## Offene Punkte gesamt
1. Akku-Schwellen am vollen Akku prüfen (Display P4).
2. Commits pushen: Octopus (`fork`), Display-Plugin, Gamepad. Die Octopus-Bridge hat kein Remote.
3. Nicht eingecheckt im Octopus-Repo: `Maschineneinstellungen.md`, `firmware.bin`, `tools/laser_test.*`, `tools/motor_test_saved.json`.
4. Geplant, noch nicht gebaut:
   - Voraussichtliches Jobende in der Job-Zeile für SD-Jobs.
   - VFD mit 0–10 V an FAN3 als zweite PWM-Spindel, Enable an FAN4 (pausiert seit 08.11.).
   - LightBurn über WLAN durch die Bridge (USART3), vorerst bleibt LightBurn an USB.
   - Kamera für LightBurn und das Display.
5. Nullpunkt-Ecke der Maschine festlegen.

## Wichtige Ports
| Gerät | Port |
|---|---|
| Octopus (USB) | COM3 |
| P4-Display (CH340, Konsole/Flash) | COM9 |
| D1 Mini (Gamepad) | COM10 |
| Octopus-Bridge S3 (CH343) | COM19 |
