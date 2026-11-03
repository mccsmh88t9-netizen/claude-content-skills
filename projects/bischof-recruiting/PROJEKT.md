# Recruiting-Video Bischof Baumpflege GmbH (Wiefelstede)

Übergabedokument, damit eine neue Sitzung nahtlos weiterarbeiten kann.

## Briefing
- Ziel: Recruiting-Video, professionell, actionreich, modern.
- Zielgruppe: Quereinsteiger ohne abgeschlossene Ausbildung mit Lust auf körperliche Arbeit, große Maschinen, Natur, Team. Zusätzlich erfahrene Baumpfleger.
- Kernbotschaft: „Du brauchst keine Vorkenntnisse. Wir zeigen dir, wie es geht!“
- Call-to-Action: https://www.bischof-baumpflege.de/jobs
- Benefits (vom Kunden bestätigt): Moderner Maschinenpark · Faire Vergütung · Vielfältige Einsätze in der Baumpflege

## Entscheidungen (freigegeben)
- Stufe 3: echtes Footage des Kunden + Seedance 2.5 über Higgsfield nur für Szene 5, Code für Schrift/Logo/Zahlen.
- Stil: Action-Trailer (eigener Stil). Stilrahmen freigegeben: `stilrahmen/stilrahmen.png`.
- Format 9:16, 1080×1920, 32 s, Musik 120 BPM (ein Schlag = 0,5 s).
- Storyboard und Sprechtext freigegeben (siehe unten).
- Higgsfield: Weg 1 (API). Nutzer hinterlegt `HIGGSFIELD_API_KEY` und erlaubt die Domains higgsfield.ai, api.higgsfield.ai, platform.higgsfield.ai.

## Stilrahmen
- Farben: Logo-Grün #12341D (Flächen), Fuhrpark-Grün #7DC243 (Signal), Knochenweiß #F4F2EC (Schrift), Schnittschutz-Orange #F26B1D (nur im Bild, nicht als Grafik).
- Schrift: Anton (Headlines, Versal), Barlow Condensed SemiBold/ExtraBold (Labels, Chips). Dateien in `fonts/`.
- Formen: grüner Balken, Benefit-Chip mit grüner Kante links, CTA-Button grün mit abgeschrägter Ecke unten rechts.
- Bewegung: Schrift schlägt auf den Beat ein (Overshoot 8 %, Nachfedern 120 ms, Wörter um 2 Frames versetzt). Kamera: Push-in 3–6 % pro Shot, nie Stillstand, Speed-Ramps auf Säge und Greifer. Schrift hinter Personen maskiert (rembg u2net). Vordergrund schneller als Hintergrund.
- Schnitt: auf Wort oder Takt. Match Cut, Maske, Whip, hart, nie zweimal derselbe Übergang hintereinander.
- Grading „Nordischer Winter“: kühle Schatten, harter Kontrast, Highlights/Himmel komprimiert, Grün und Orange satt, Vignette, 35-mm-Korn. Obere Bildkante leicht abgedunkelt für die Brand-Zeile.
- Safe Zone: untere ~380 px ohne wichtige Inhalte (Reels/TikTok-UI).
- Vorbild: Kampagnen von Workwear- und Outdoor-Marken.

## Storyboard und Sprechtext

| Zeit | Bild | Schrift | Sprechtext | Übergang |
|---|---|---|---|---|
| 0:00–0:02 | Schwarz + Anwerfzug-Sound, dann Säge im Stamm, Späne in Zeitlupe (`DJI_20260106_111921_962`) | KEINE AUSBILDUNG? | „Keine Ausbildung?“ | harter Schnitt |
| 0:02–0:05 | Kletterer am Greifer schwebt hoch (`IMG_0209`, ~12,5 s) | EGAL. hinter dem Kletterer maskiert | „Egal.“ | Match Cut Aufwärtsbewegung |
| 0:05–0:08 | Blick aus Hubsteiger-Korb auf Team + Häcksler (`IMG_0469`) | ANPACKEN. + grüner Balken | „Bei uns zählt nur eins: dass du anpacken willst.“ | Maske über Korbrand |
| 0:08–0:12 | Stakkato je 1 Takt: Greifer packt Stamm (`IMG_0472`) · Häckslertrommel (`DJI_20260131_090238_114`) · Ast in Häcksler (`IMG_0477`) · Hubsteiger im Schnee (`DJI_20260131_091040_966`) | GROSSE MASCHINEN. ECHTE NATUR. JEDES WETTER. | „Große Maschinen. Echte Natur. Bei jedem Wetter.“ | Whip Pans |
| 0:12–0:17 | Anlernszene: Kollege zeigt Neuem Griff an der Säge / Knoten, Nahaufnahme Hände — **Seedance 2.5** | DU BRAUCHST KEINE VORKENNTNISSE. | „Du brauchst keine Vorkenntnisse.“ | harter Schnitt in die Stille |
| 0:17–0:21 | Beat-Drop: Mitarbeiter zieht Äste (`IMG_0474`), Stammstück fällt (`DJI_20260106_111921_962`, Ende) | WIR ZEIGEN DIR, WIE'S GEHT. | „Wir zeigen dir, wie's geht.“ | harter Schnitt auf Drop |
| 0:21–0:25 | Fotos MAN-Lkw + Teleskoplader mit Parallax (`stills/`) | Chips: Moderner Maschinenpark · Faire Vergütung · Vielfältige Einsätze | „Moderner Maschinenpark. Faire Vergütung. Jeden Tag ein anderer Einsatz.“ | grüne Wischblende |
| 0:25–0:27 | Kletterer hoch oben (`IMG_0209`) | QUEREINSTEIGER? PROFI? BEIDE. | „Ob Quereinsteiger oder Profi: Wir wollen dich.“ | Zoom-Schnitt |
| 0:27–0:32 | Lkw-Front mit Blitzer (`IMG_0460`), Blitz wird Match Cut auf Logo | Logo, JETZT BEWERBEN, bischof-baumpflege.de/jobs | „Bischof Baumpflege aus Wiefelstede. Jetzt bewerben.“ | Licht-Match-Cut |

Ton: Originalgeräusche aus dem Footage (Säge, Häcksler, Hydraulik) + Musik + Sprecher (jung, kernig, männlich, kein Werbeton). Musik/Stimme/SFX aus Higgsfield.

## Regeln aus dem Auftrag
- Vor jeder Higgsfield-Erzeugung Kosten in Credits und Euro nennen, mit dem echten Auftrag abfragen, Guthaben prüfen. Teurer als angesagt → vorher fragen.
- Preis pro Credit: **noch offen, beim Nutzer erfragen.**
- Schrift, Zahlen, Logos immer aus Code.
- Stil-Check nach jeder Szene mit Standbildern; am Ende Gesamtcheck, dann MP4 liefern.

## Material
- `footage/` – 9 Originalclips des Kunden, alle hochkant (Rotation in Metadaten, ffmpeg dreht automatisch).
- `stills/` – Logo (PNG, weißer Hintergrund), Fotos Teleskoplader, Hubsteiger-Korb, MAN-Lkw. Ein Screenshot einer Feuerwehr-App wurde versehentlich mitgeschickt und wird nicht genutzt.
- `stilrahmen/` – Stilrahmen-Quellen (`board.html`, gerendert mit `node shot.js <html> <png>`), freigestelltes Logo `logo.png`, Kletterer-Maske.

## Werkzeuge
- ffmpeg, Playwright/Chromium (HTML-Frames rendern), Python mit PIL/numpy, `pip install rembg onnxruntime` für Freistellung.
- Google Fonts/jsdelivr sind im Netz gesperrt; Schriften kamen von raw.githubusercontent.com.

## Stand (03.11.2026)
- Render-Pipeline steht: `render/build.py` (Szenen, Typo, Übergänge) + `render/look.py` (Grading, Korn, Typo-Bausteine).
  - `python3 render/build.py` → `render/out/video_stumm.mp4` (32 s, 1080×1920, 30 fps, ohne Ton)
  - `python3 render/build.py --stills` → Stil-Check-Standbilder in `render/out/stills/`
  - `--range a:b` rendert nur Frames a–b. Personenmasken werden in `render/cache/` gecacht (nicht im Git).
- Szenen 1–4 und 6–9 aus echtem Footage gebaut, Stil-Check bestanden. Szene 5 (0:12–0:17) ist ein dunkelgrüner Platzhalter mit fertiger Typo.
- Korrigiert nach Stil-Check: Ortszeile Endkarte („AUS WIEFELSTEDE“), dunkler Verlauf hinter Schrift in Szene 6, Richtung der grünen Wischblende.
- Abweichung: Higgsfield läuft jetzt über den MCP-Connector statt über den API-Key (Weg 1 entfällt).

## Higgsfield-Kosten Szene 5 (Abfrage 03.11.2026, nichts erzeugt)
- Guthaben: **80 Credits**, Plan Basic.
- Seedance 2.5, 5 s, 9:16, 1080p, ohne Ton: **80 Credits** (= gesamtes Guthaben).
- Seedance 2.5, Entwurf 480p, 5 s: **15 Credits** (kann später auf 1080p finalisiert werden, Finalisierung wird extra berechnet).
- Sprecher, Musik, SFX noch nicht abgefragt, passen nach einer 1080p-Szene 5 nicht mehr ins Guthaben.
- Euro-Preis pro Credit weiterhin offen.

## Nächste Schritte
1. Nutzer entscheidet: Szene 5 als Entwurf (15 Credits) oder direkt 1080p (80 Credits), ggf. Credits nachkaufen. Euro-Preis pro Credit erfragen.
2. Szene 5 erzeugen, in `build.py` als Shot einsetzen (Platzhalter ersetzen), Stil-Check.
3. Sprecher, Musik (120 BPM), SFX abfragen und erzeugen, Ton mischen, Gesamt-Stil-Check, finales MP4.
