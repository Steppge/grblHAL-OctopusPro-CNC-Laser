# Maschineneinstellungen – CNC/Laser mit BTT Octopus Pro (grblHAL)

Stand: 01.11.2026, Motoren und Treiber 15.11.2026. Werte aus dieser Sitzung (ausgelesen mit `$$` bzw. selbst eingestellt), nicht frisch
vom Board gelesen. Vor dem Einrichten von LightBurn einmal `$$` lesen und vergleichen.

## Hardware

| Teil | Typ |
|---|---|
| Steuerung | BTT Octopus Pro v1.0 (STM32F446), grblHAL (Fork Steppge/grblHAL-OctopusPro-CNC-Laser, Branch `octopus-pro-joy`) |
| Treiber | 4× BTT TMC5160T Pro V1.0 über SPI (R sense 75 mΩ), SpreadCycle, 16 Mikroschritte |
| Motorspannung | 48–50 V (Labornetzteil, max. 4 A) an MOTOR_POWER; Board 24 V |
| Motoren X, Y, Y2 | Nidec Servo KH56KM2-951 (NEMA 23, 2,0 A, 0,93 Nm, 1,32 Ω, 3,19 mH, 2,4 V; Datenblatt `OneDrive\Dokumente\KH56KM2.pdf`) |
| Motor Z | StepperOnline 17HE19-2004S (NEMA 17, 2,0 A, ca. 0,55 Nm; R/L ungeprüft, etwa 1,4 Ω / 3 mH) |
| Y | gekoppelt (Y + Y2) mit Auto-Squaring, zwei Schalter |
| Laser | LaserTree LT-80W-AA-PRO, 24-V-Version, 10 W optisch, PWM 0–5 kHz |
| Bedienung | CrowPanel 9" ESP32-P4 Display (USART2), PS4-Gamepad über D1 Mini ESP32 (USART1) |
| Verbindung PC | **USB direkt am Octopus** (STM32 Virtual COM, bisher COM3) |

## Achsen

| | X | Y | Z |
|---|---|---|---|
| Schritte/mm (`$100–102`) | 640 (5 mm/Umdr.) | 400 (8 mm/Umdr.) | 1600 (2 mm/Umdr.) |
| Höchstgeschwindigkeit (`$110–112`) | **4500 mm/min** | **4500 mm/min** | **1500 mm/min** |
| Beschleunigung (`$120–122`) | **500 mm/s²** | **500 mm/s²** | **250 mm/s²** |
| Verfahrweg (`$130–132`) | 290 mm | 235 mm | 212 mm |
| Arbeitsbereich nach Referenzfahrt | 0 … 287 | 0 … 232 | −209 … 0 |
| Motorstrom (`$140–142`) | 1600 mA (vorher 1800, X-Motor ca. 55 °C; nicht weiter senken) | 1300 mA (Y und Y2) | 1400 mA |
| Mikroschritte (`$150–152`) | 16 | 16 | 16 |

Getestet ohne Schrittverlust (24.10.2026, Messung am Referenzschalter): X bis 4500 mm/min bei 700 mm/s²
(ab 700 hörbar) und 6500 mm/min bei 160 mm/s²; Y bis 4500 bei 500 mm/s² und 7000 bei 160 mm/s²;
Z bis 2000 bei 90 mm/s² und 1500 bei 250 mm/s². X bei 6000 mm/min mit 400 mm/s²: Schrittverlust.

## Motoren und Treiber (TMC5160, 48 V)

- SpreadCycle auf allen Achsen (`TMC_x_STEALTHCHOP 0`), Haltestrom 50 %.
- Chopper mit den Standardwerten aus `trinamic/tmc5160.h`: toff 5, tbl 1, hstrt 3, hend 5 (Summe 8). Überschlag
  nach Trinamic-Datenblatt für 48 V und 3,19 mH: die Hysterese passt etwa, viel ist am Chopper nicht zu holen.
- Ändern ohne Neubau: `M919 X O<toff> P<hend> S<hstrt>` (nicht gespeichert, `M919` allein zeigt die Werte).
  Dauerhaft: `TRINAMIC_EXTENDED_SETTINGS 1` in `my_machine.h`, dann `$651–$657` (für alle Achsen gemeinsam).
  Marlins `CHOPPER_DEFAULT_24V/48V` gibt es in grblHAL nicht.
- X-Motor wird beim Fahren heiß (seit 48 V mehr Eisenverluste): bei 1,6 A etwa 6,8 W Kupferverlust, unter dem
  Nennstrom. Lösung: **Aluminium-Kühlkörper NEMA 23** mit Wärmeleitpad (bestellen, 15.11.2026), danach
  10 min fahren und die Gehäusetemperatur messen (bis etwa 80 °C unkritisch). Lüfter mit Halter als nächste Stufe.

## Laser / Spindel

| Einstellung | Wert |
|---|---|
| `$32` Laser-Modus | 1 (an) |
| `$30` S max | 1000 |
| `$31` S min | 0 |
| `$33` PWM-Frequenz | 4000 Hz (Laser erlaubt bis 5 kHz) |
| `$34`, `$35` PWM aus/min | 0 / 0 |
| `$36` PWM max | 100 % |
| Spindel-Ausgänge | PWM FAN0 (PA8), Enable Bett-Ausgang (PA1), Richtung FAN5 (PD15) |

## Referenzfahrt und Grenzen

| Einstellung | Wert |
|---|---|
| `$22` Homing | 591 (an, Referenzfahrt nach dem Einschalten nötig) |
| `$23` Homing-Richtung invertiert | 3 = X und Y fahren zum Minimum, Z nach oben |
| `$27` Freifahrweg | 3 mm |
| `$20` Software-Grenzen | 1 (an) |
| `$21` Hardware-Grenzen | 3 (an, strikt) |
| `$40` Jog innerhalb der Grenzen | 1 |
| `$1` Haltezeit der Motoren | 60000 ms |
| Z-Schalter | ungenau (Streuung ca. 0,01 mm), soll getauscht werden |

## Für LightBurn

- Gerätetyp **GRBL**, Verbindung **seriell/USB** (COM-Port des Octopus).
- **S-Wert max = 1000** (wie `$30`).
- Laser-Modus ist an (`$32=1`): dynamische Leistung mit M4 funktioniert.
- Arbeitsbereich: **287 × 232 mm** (X × Y).
- **Overscan** bei 4500 mm/min und 500 mm/s²: v² / (2·a) ≈ **5,6 mm** – mit Reserve 6–8 mm.
- **Nullpunkt / Ursprung: hinten rechts** → in LightBurn **Ursprung oben rechts**.
  X-Schalter rechts, zwei Y-Schalter (links und rechts, je einer pro Y-Motor) hinten.
  Damit fährt **+X nach links** und **+Y nach vorne** (per Jog-Test bestätigt, 01.11.2026).
- „Start von“: **Absolute Koordinaten**; Auto-Home beim Start an (`$22`).
- **Z-Achse** in LightBurn genutzt: Z-Achse aktivieren an, **nur relative Z-Bewegungen an**
  (Z = 0 oben, Bereich −209 … 0). Z+ muss nach oben fahren, sonst „Z-Richtung umkehren“ einschalten.
  Fokus von Hand (Gamepad/Display), in den Ebenen Z-Versatz und Z-Schritt pro Durchgang.
- Höchstgeschwindigkeit in LightBurn nicht über 4500 mm/min (Z 1500).
- Vor dem Verbinden PC-Deck.exe beenden (blockiert sonst COM3).

## Weitere Hinweise

- Nach einem Programm am PC, das den USB-Port ohne DTR schließt, warten Display- und Gamepad-Befehle,
  bis ein Programm den Port wieder öffnet oder das Board neu startet (LightBurn trennt sauber).
- Die TMC5160 brauchen ihre 48 V vor oder gleichzeitig mit den 24 V des Boards; 48 V nachträglich
  zugeschaltet: danach Octopus neu starten.
- Gamepad (Plugin 1.4, Empfänger 1.6): Joggen, Home, X0Y0 und Z0 nur mit Freigabe (Options); im Alarm nur Home.
