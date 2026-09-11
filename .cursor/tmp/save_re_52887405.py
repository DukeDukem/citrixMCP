# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Ute Holst,

vielen Dank, dass Sie uns die Sofortüberweisung über 127,98 Euro und Ihre Frage zur Entsperrung Ihres Anschlusses mitgeteilt haben.

Es ist verständlich, dass Sie nach der Zahlung möglichst schnell wieder telefonieren bzw. Ihr Gerät nutzen möchten.

Anfragen zu Sperrung und Zahlungseingang werden von der zuständigen Fachabteilung für Zahlungsthemen bearbeitet; Ihre Anfrage wurde dorthin weitergeleitet.

Zur Orientierung: Nach Zuordnung der Zahlung auf Ihrem Kundenkonto erfolgt die Entsperrung in der Regel automatisch innerhalb von etwa 48 Stunden. Ob die Zahlung bereits verbucht ist, prüfen Sie in Mein o2 unter o2.de bzw. in der Mein o2 App unter Rechnung / Jahresübersicht (Ihre genannte Rechnung endet auf 672). Wichtig ist, dass im Verwendungszweck die korrekte Kundennummer stand.

Zusätzlich hilft der Mahnwesen-Chat unter o2.de/mahnwesen-chat (Mo–Fr 8–18 Uhr), falls die Sperre nach Verbuchen der Zahlung länger bestehen bleibt.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

assert "6028931672" not in text
assert text.count("Guten Tag") == 1
assert "Fall #" not in text
assert "Ute Holst" in text

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52887405.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52887405", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
