# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

text = """Guten Tag Klaus Andre Hiby,

vielen Dank, dass Sie uns die Probleme in Mein o2 geschildert und einen Screenshot beigefügt haben – insbesondere dass viele Bereiche nicht nutzbar sind, Nachrichten ausgegraut erscheinen und Ihr beauftragter LWL-/DSL-Vertrag nicht sichtbar ist.

Es ist verständlich, dass Sie Ihren Glasfaser-/DSL-Auftrag und Ihre Nachrichten im Portal einsehen möchten und der aktuelle Zustand Sie behindert.

Bitte prüfen Sie zunächst diese Schritte:
- Melden Sie sich unter o2.de bei Mein o2 ab und erneut an; testen Sie ggf. einen anderen Browser oder den Inkognito-Modus.
- Falls Ihr Festnetzanschluss bereits freigeschaltet ist und Sie eine Festnetznummer erhalten haben: registrieren bzw. melden Sie sich mit dieser Festnetznummer als Benutzername an – erst dann ist der volle Kundenbereich für Festnetz oft vollständig verfügbar.
- Prüfen Sie nach dem Login oben den Vertragswechsel (Dropdown), falls mehrere Verträge oder Kundennummern hinterlegt sind.
- Den Auftragsstatus zu LWL/DSL finden Sie häufig auch in Ihren Bestätigungs-E-Mails von o2; wichtige Infos erreichen Sie dort auch, wenn einzelne Menüpunkte im Portal noch ausgegraut sind.
- Ausgegraute „Nachrichten“ betreffen in vielen Fällen nur Hinweise ohne Vertragsrelevanz; der eigentliche Auftragsfortschritt kommt per E-Mail/SMS/Brief.

Sollte der LWL-/DSL-Vertrag danach weiterhin fehlen oder Menüpunkte gesperrt bleiben, antworten Sie bitte auf diese E-Mail mit Ihrer Kundennummer und – sofern vorhanden – Ihrer Festnetznummer. Dann können wir den Zugang gezielt zuordnen.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""

root = Path(r"c:\Users\PC ENTER\Desktop\Citrix")
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "temp_reply_52886378.txt").write_text(text.strip() + "\n", encoding="utf-8")
rec = {"case_id": "#52886378", "response_text": text.strip(), "saved_at": time.time()}
(root / ".cursor" / "skills" / "sprinklr-write-reply" / "latest_re_reply.json").write_text(
    json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
)
assert text.count("Guten Tag") == 1 and "Fall #" not in text
print("OK", len(text.strip()))
