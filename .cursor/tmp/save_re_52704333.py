# -*- coding: utf-8 -*-
import json
import time
from pathlib import Path

text = """Guten Tag Christian Bläsi,

vielen Dank für Ihre Kündigung des o2 International Pack 60 zum nächstmöglichen Zeitpunkt.

Es ist verständlich, dass Sie diese Zusatzoption beenden und eine schriftliche Bestätigung des Beendigungszeitpunkts wünschen.

Sie können die Abbestellung bequem selbst in Mein o2 vornehmen bzw. den Status prüfen:

1. Melden Sie sich unter o2.de bzw. in der Mein o2 App an und öffnen Sie Tarif & Optionen (bzw. Tarif & SIM).
2. Wählen Sie beim International Pack 60 „Option bearbeiten“ und buchen Sie „International Voice Standard“ – damit wird das International Pack 60 zum nächstmöglichen Zeitpunkt ersetzt bzw. beendet.
3. Alternativ können Sie über https://www.o2online.de/service/kuendigung/ eine Kündigung einreichen und im Freitext ausdrücklich „o2 International Pack 60“ angeben (nicht den gesamten Mobilfunkvertrag).

Den Beendigungszeitpunkt sehen Sie anschließend in Mein o2 bei den Optionsdetails. Bitte antworten Sie bei Rückfragen mit dem bisherigen E-Mail-Verlauf.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
reply_path = root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52704333.txt"
reply_path.write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52704333", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
