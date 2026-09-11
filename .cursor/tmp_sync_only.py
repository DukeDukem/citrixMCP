from pathlib import Path
import json, time
text = """Guten Tag Rebecca Köppl,

vielen Dank, dass Sie uns über die weiterhin eintreffenden Briefe an Jorg Weber unter der Adresse Höfleser Hauptstraße 69a in 90427 Nürnberg informiert haben.

Ich verstehe gut, dass der Aufwand, diese Post dauerhaft zu entsorgen oder zurückzusenden, für Sie belastend ist.

Adress- und Vertragsdaten können wir aus Datenschutzgründen nur auf Veranlassung des jeweiligen Vertragsinhabers ändern. Bitte geben Sie Herrn Weber – sofern möglich – den Hinweis, die Kontaktadresse in Mein o2 (App oder o2.de) unter den persönlichen Daten zu aktualisieren bzw. den Vertrag dort zu prüfen. Briefe, die nicht für Sie bestimmt sind, können Sie mit dem Vermerk „Unbekannt verzogen / Nicht annahmeberechtigt“ an den Absender zurückgeben.

Eine Bestätigung, dass die Adresse in unseren Systemen bereits gesperrt oder gelöscht wurde, kann ich Ihnen in dieser E-Mail nicht zusichern.

Zur Verbesserung unseres Kundenservices erhalten Sie möglicherweise eine E-Mail oder SMS zu einer Zufriedenheitsbefragung. Wenn Sie mit meinem Service zufrieden waren, freue ich mich sehr über eine positive Bewertung, bei der die 10 der Höchstbewertung entspricht.

Freundliche Grüße,

Ihr o2 Kundenbetreuer
Lukasz Kowalski

Telefónica Germany GmbH & Co. OHG - Georg-Brauchle-Ring 50 - 80992 München - Deutschland - o2.de

Ein Beitrag zum Umweltschutz. Nicht jede E-Mail muss ausgedruckt werden.

Bitte finden Sie hier die handelsrechtlichen Pflichtangaben: telefonica.de/pflichtangaben

* gemäß Tarif für Anrufe in das dt. Fest- bzw. Mobilfunknetz"""
base = Path(".cursor/skills/sprinklr-write-reply")
(base / "reply_57173377.txt").write_text(text.strip() + "\n", encoding="utf-8")
payload = {"case_id": "#57173377", "response_text": text.strip(), "saved_at": int(time.time()), "source": "re_section6"}
for n in ("latest_re_reply.json", "latest_user_directed_reply.json"):
    (base / n).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
(base / "latest_re_reply.txt").write_text(text.strip() + "\n", encoding="utf-8")
print("draft_ok", len(text))
