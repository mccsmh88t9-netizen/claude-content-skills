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
- Preis pro Credit: **0,05 €** (vom Nutzer bestätigt).
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
- Erledigt: Szenen 1–4 und 6–9 aus echtem Footage, Stil-Check pro Szene + Gesamtcheck (Kontaktbögen in `work/check/`). Szene 5 als Platzhalter mit finaler Schrift.
- Pipeline in `work/`: `grade.py` (LUT `nordic.cube`), `engine.py` (Dekodierung HLG->SDR, Kamera, Typo, Masken, Korn), `scenes.py` (alle Timings in Frames, 30 fps, 1 Schlag = 15 Frames), `render.py`.
- Rendern: `cd work && python3 render.py 1 2 3 4 5 6 7 8 9 concat` -> `work/out/video_stumm.mp4` (≈4 min, Caches in `work/cache/`, nicht im Repo).
- Szene 5 einsetzen: Seedance-Clip als `footage/seedance_s5.mp4` ablegen (9:16, ≥5 s), dann `python3 render.py 5 6 concat`.
- Lesart Storyboard: Spalte „Übergang“ = Übergang IN die Szene. Folge: S1 hart aus Schwarz, S2 Match Cut aufwärts, S3 Korbrand-Maske, S4 Whips, S5 hart in die Stille, S6 hart auf Drop, S7 grüne Wischblende, S8 Zoom-Schnitt, S9 Licht-Match-Cut auf Logo. S5/S6 sind zwei harte Schnitte hintereinander (so freigegeben; Unterschied liegt im Ton).
- Netz: Nutzer hat am 03.11. `docs.higgsfield.ai`, `upload.higgsfield.ai`, `pixabay.com`, `cdn.pixabay.com` freigegeben (neue Sitzung nötig, erst prüfen).

## Higgsfield-Stand (03.11.2026)
- Zugriff über den **Higgsfield-MCP-Connector** (`mcp__Higgsfield__*`), nicht über die REST-API. Kosten vorab mit `get_cost: true`.
- Guthaben: **80 Credits**, Plan **basic**. Seedance 2.5 wurde abgelehnt: „Requires plus plan or higher“ (nichts abgebucht). **Vor dem nächsten Versuch beim Nutzer klären: auf Plus upgegradet? Sonst Alternativmodell mit Kosten vorschlagen.**
- Abgefragte Kosten (9:16): Seedance 2.5 5 s 1080p = 80 Cr (4,00 €, mit/ohne Ton gleich) · 720p = 35 Cr · Entwurf 480p = 15 Cr (Finalisierung wird voll berechnet) · Sprecher ganzer Text ElevenLabs v4 = 1,84 Cr (0,09 €) · Seed Audio = 2,4 Cr.
- Freigegeben vom Nutzer: Budget ca. 4,30 € (Szene 5 in 1080p + 2–3 Sprecherproben). 80 Cr reichen nicht für beides, ca. 6 Cr fehlen; Szene 5 hat Vorrang.
- Referenzbild für Szene 5: `work/seedance/ref_ausruestung.jpg` (Upload: `media_upload` -> curl PUT mit Header `If-None-Match: *` -> `media_confirm`, dann `mode: omni_reference`, Rolle `image_references`; Preis vorher neu mit get_cost prüfen).
- Prompt Szene 5 (t2v, duration 5, resolution 1080p, aspect_ratio 9:16, generate_audio true):
  „Vertical 9:16 cinematic close-up, documentary workwear-campaign look. Two arborists in a snowy winter forest clearing with freshly cut logs and sawdust. The experienced mentor wears an orange chainsaw-protective jacket under a dark navy padded vest, black gloves, red helmet with red ear defenders and mesh visor. He stands beside a young newcomer in the same gear and guides the newcomer's gloved hands onto an orange chainsaw: right hand onto the rear handle, left hand wrapping the front grip, then he taps the chain brake with his thumb and gives a short approving nod. Camera stays tight on the hands and the saw, faces partly cropped or out of focus, shallow depth of field. Overcast cold daylight, cool blue shadows, saturated orange, slow steady push-in, slight handheld energy, 35mm film grain, realistic. Ambient sound: quiet winter forest, gloves on plastic handle, a soft click of the chain brake, no music, no speech. No text, no logos.“
- Ergebnis als `footage/seedance_s5.mp4` ablegen, dann `python3 render.py 5 6 concat`.
- Sprecher: Stimmenliste (`list_voices`) nennt keine Sprache -> 2–3 männliche Kandidaten (z. B. Knox, Brooks, Marcus) mit ElevenLabs v4 erzeugen und dem Nutzer zur Auswahl schicken.
- Musik: Higgsfield hat kein freigegebenes Musik-/SFX-Modell (Suno fehlt, Sonilo/Mirelo nur für Spiele). Nutzer will **lizenzfreie Musik** -> Pixabay (Pixabay-Lizenz, kommerziell, ohne Nennung), Action-Trailer, ~120 BPM, Drop bei 0:17, Stille in Szene 5. Lizenz/Quelle im Repo dokumentieren.
- Geräusche: Originalton aus dem Footage (Säge, Häcksler, Hydraulik).

## Nächste Schritte
2. Nach Freischaltung: Higgsfield-Kosten für Szene 5 (Seedance 2.5), Sprecher, Musik, SFX abfragen und dem Nutzer nennen.
3. Ton mischen, Gesamt-Stil-Check, MP4 rendern und liefern.
