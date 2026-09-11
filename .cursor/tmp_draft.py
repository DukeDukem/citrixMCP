from pathlib import Path
import json, time
text = """Guten Tag Björn Höppe,

vielen Dank für Ihre Nachricht zur Geschwindigkeit Ihres
freigeschalteten DSL-Zugangs. Sie erwarten 100 Mbit laut
Vertrag, messen aber derzeit etwa 30 Mbit Download und
etwa 13,5 Mbit Upload.

Ich verstehe gut, dass diese Abweichung für Sie ärgerlich
ist und Sie eine spürbare Verbesserung brauchen.

Bitte prüfen Sie zuerst Folgendes:
- Router neu starten und per LAN-Kabel am Router messen
  (nicht nur WLAN).
- Unter Mein o2 (App oder o2.de) den Anschlussstatus und
  Hinweise zu Störungen einsehen.
- Einen Geschwindigkeitstest möglichst zu verschiedenen
  Tageszeiten wiederholen und das Ergebnis notieren.

Antworten Sie bitte kurz mit Ihrer Kundennummer mit 1132
am Ende sowie dem gemessenen Download/Upload (LAN) und
ob der Router über Kabel oder WLAN getestet wurde. So
kann die Abweichung zur vertraglichen 100-Mbit-Angabe
besser eingeordnet werden.

Zur Verbesserung unseres Kundenservices erhalten Sie
möglicherweise eine E-Mail oder SMS zu einer
Zufriedenheitsbefragung. Wenn Sie mit meinem Service
zufrieden waren, freue ich mich sehr über eine positive
Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG -
Georg-Brauchle-Ring 50 - 80992 München - Deutschland -
o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss
ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen
Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw.
Mobilfunknetz"""
base = Path(".cursor/skills/sprinklr-write-reply")
(base / "reply_57173780.txt").write_text(text.strip() + "\n", encoding="utf-8")
payload = {"case_id": "#57173780", "response_text": text.strip(), "saved_at": int(time.time()), "source": "re_section6"}
for n in ("latest_re_reply.json", "latest_user_directed_reply.json"):
    (base / n).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
(base / "latest_re_reply.txt").write_text(text.strip() + "\n", encoding="utf-8")
print("draft_ok", len(text))
