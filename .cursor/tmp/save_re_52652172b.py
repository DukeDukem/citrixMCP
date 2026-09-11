# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Sabrina Beckers,

vielen Dank, dass Sie uns Ihre Kundennummer und die letzten vier Stellen Ihrer IBAN übermittelt haben und uns erneut auf den nicht nutzbaren Internetanschluss sowie die berechnete Router-Grundgebühr aufmerksam machen.

Es ist nachvollziehbar, dass Sie den Anschluss seit Erhalt des Routers nicht nutzen können und die Abrechnung der Grundgebühr trotz der telefonischen Zusage als ungerecht empfinden.

Zu Ihrem Internetanschluss können Sie jetzt Folgendes prüfen:
- Live-Check / Störungsprüfung unter o2.de bzw. o2online.de/service/internet-festnetz-stoerung sowie die o2 my Service App für automatische Verbindungstests.
- Router neu starten: Netzstecker ca. 20–30 Sekunden ziehen, wieder einstecken und etwa eine Minute warten.
- Verkabelung prüfen und testweise per LAN-Kabel (nicht nur WLAN) verbinden.
- Routerhilfe und LED-Hinweise unter o2.de/routerhilfe.

Damit wir das Störungsbild besser eingrenzen können, teilen Sie uns bitte zusätzlich mit:
- wie die Leuchten am Router aussehen (z. B. dauerhaft rot, blinkend, aus),
- ob gar keine Verbindung besteht oder nur Abbrüche,
- welches Router-Modell Sie haben,
- ob das Problem auch per LAN-Kabel besteht.

Zur Router-Grundgebühr: Bitte prüfen Sie in Mein o2 unter Rechnung die betroffene Position. Wenn dort weiterhin eine Grundgebühr ausgewiesen ist, die Ihnen telefonisch erlassen werden sollte, antworten Sie gerne mit dem Rechnungsdatum bzw. der Rechnungsnummer (ohne den vollständigen Betragsverlauf zu wiederholen). Wir können dann die Position anhand Ihres Vertrags mit der Kundennummer mit 749 am Ende zuordnen.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

# strip accidental full KN/IBAN
assert "6068017749" not in text
assert "1014" not in text or "IBAN" in text  # we said last four not in body - avoid 1014
# remove IBAN digits entirely from customer body
assert "1014" not in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52652172.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52652172", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
