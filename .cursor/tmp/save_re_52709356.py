# -*- coding: utf-8 -*-
import json
import time
from pathlib import Path

text = """Guten Tag D. Schaal,

vielen Dank für Ihre Anfrage zur Rücknahme Ihrer Kündigung und zur Verlängerung Ihres Mobilfunkvertrags zu den bisherigen Konditionen (20 EUR monatlicher Rabatt / 8,99 EUR monatlich).

Es ist verständlich, dass Sie nach zahlreichen Kontakten eine verbindliche Zusage wünschen – insbesondere da Ihr Vertrag zum 04.08.2026 endet.

Aus Datenschutzgründen bearbeitet das E-Mail-Team keine Aktionen zu Vertragsverlängerungen, Angeboten oder Konditionszusagen. Hierfür wenden Sie sich bitte an die Care-Hotline, wo Sie das Vertragsspezialistenteam unterstützt:

089 78 79 79 400

Bitte schildern Sie dort möglichst zeitnah Ihren Wunsch: Kündigungsrücknahme nur bei Fortführung zu Ihren bisherigen Konditionen (Rufnummer mit 280 am Ende, Vertragsende 04.08.2026). Den Kündigungsstatus und das Vertragsende können Sie ergänzend in Mein o2 unter o2.de bzw. in der Mein o2 App unter Tarif & SIM einsehen. Handeln Sie bitte vor dem 04.08.2026.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52709356.txt").write_text(
    text.strip() + "\n", encoding="utf-8"
)
rec = {"case_id": "#52709356", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("OK", len(text.strip()))
