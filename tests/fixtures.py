"""Broker exports in the real formats, with invented content.

Every quirk here was read off an actual export: the two blank column
headers, the French descriptions, the comma decimals, the `@` before the
price, Trade Republic putting an ISIN in a column called `symbol`. The
numbers, dates and names are made up.
"""

# Degiro Account.csv. Note the header: `Change` and `Balance` each name a
# CURRENCY, and the blank column after each holds the amount. A
# DictReader collapses both blanks into one key and the second wins,
# which silently turns every change amount into a balance amount.
DEGIRO_CSV = """Date,Time,Value date,Product,ISIN,Description,FX,Change,,Balance,,Order Id
24-04-2026,08:55,24-04-2026,,,Degiro Cash Sweep Transfer,,EUR,"-40,80",EUR,"109,42",
23-04-2026,15:02,23-04-2026,iShares Core MSCI World,IE00B4L5Y983,"Achat 71 iShares Core MSCI World UCITS ETF USD (Acc)@112,5 EUR (IE00B4L5Y983)",,EUR,"-7987,50",EUR,"150,22",abc-1
23-04-2026,15:02,23-04-2026,iShares Core MSCI World,IE00B4L5Y983,Frais DEGIRO de courtage et/ou de parties tierces,,EUR,"-3,90",EUR,"8137,72",abc-1
20-04-2026,09:00,20-04-2026,Norwest Minerals Ltd,AU0000025280,"Vente 1 Norwest Minerals Ltd@0,011 AUD (AU0000025280)",,EUR,"0,01",EUR,"8141,62",xyz-9
15-04-2026,00:00,15-04-2026,Koninklijke Ahold,NL0000235190,Dividende,,EUR,"12,34",EUR,"8141,61",
15-04-2026,00:00,15-04-2026,Koninklijke Ahold,NL0000235190,Impôts sur dividende,,EUR,"-1,85",EUR,"8129,27",
10-04-2026,11:20,10-04-2026,,,Dépôt flatex,,EUR,"1000,00",EUR,"8131,12",
09-04-2026,11:20,09-04-2026,,,Frais de connexion aux places boursières 2026,,EUR,"-2,50",EUR,"7131,12",
08-04-2026,10:00,08-04-2026,,,Opération de change - Débit,1.0921,EUR,"-25,00",EUR,"7133,62",
07-04-2026,10:00,07-04-2026,Some Closed Position,LU0000000009,"Vente 5 Some Closed Position@10,0 EUR (LU0000000009)",,EUR,"50,00",EUR,"7158,62",clo-2
06-04-2026,10:00,06-04-2026,Some Closed Position,LU0000000009,"Achat 5 Some Closed Position@9,0 EUR (LU0000000009)",,EUR,"-45,00",EUR,"7108,62",clo-1
"""

# Same account, an overlapping export downloaded a week later: the first
# three rows repeat, then two new ones. Re-importing must add only the
# new ones.
DEGIRO_CSV_OVERLAPPING = """Date,Time,Value date,Product,ISIN,Description,FX,Change,,Balance,,Order Id
30-04-2026,09:10,30-04-2026,,,Dépôt flatex,,EUR,"500,00",EUR,"609,42",
28-04-2026,14:00,28-04-2026,iShares Core MSCI World,IE00B4L5Y983,"Achat 4 iShares Core MSCI World UCITS ETF USD (Acc)@113,0 EUR (IE00B4L5Y983)",,EUR,"-452,00",EUR,"109,42",def-2
24-04-2026,08:55,24-04-2026,,,Degiro Cash Sweep Transfer,,EUR,"-40,80",EUR,"109,42",
23-04-2026,15:02,23-04-2026,iShares Core MSCI World,IE00B4L5Y983,"Achat 71 iShares Core MSCI World UCITS ETF USD (Acc)@112,5 EUR (IE00B4L5Y983)",,EUR,"-7987,50",EUR,"150,22",abc-1
23-04-2026,15:02,23-04-2026,iShares Core MSCI World,IE00B4L5Y983,Frais DEGIRO de courtage et/ou de parties tierces,,EUR,"-3,90",EUR,"8137,72",abc-1
"""

# The same file a German-language account would produce. Nothing in the
# parser may depend on the verb being "Achat".
DEGIRO_CSV_GERMAN = """Date,Time,Value date,Product,ISIN,Description,FX,Change,,Balance,,Order Id
23-04-2026,15:02,23-04-2026,iShares Core MSCI World,IE00B4L5Y983,"Kauf 71 iShares Core MSCI World UCITS ETF USD (Acc)@112,5 EUR (IE00B4L5Y983)",,EUR,"-7987,50",EUR,"150,22",abc-1
20-04-2026,09:00,20-04-2026,Norwest Minerals Ltd,AU0000025280,"Verkauf 1 Norwest Minerals Ltd@0,011 AUD (AU0000025280)",,EUR,"0,01",EUR,"8141,62",xyz-9
"""

TRADE_REPUBLIC_CSV = (
    '"datetime","date","account_type","category","type","asset_class","name",'
    '"symbol","shares","price","amount","fee","tax","currency","original_amount",'
    '"original_currency","fx_rate","description","transaction_id",'
    '"counterparty_name","counterparty_iban","payment_reference","mcc_code"\n'
    '"2026-05-01T03:49:10.717832Z","2026-05-01","DEFAULT","CASH","INTEREST_PAYMENT",'
    '"","","","","","0.800000","","-0.24","EUR","","","","Interest payment",'
    '"11111111-1111-1111-1111-111111111111","","","",""\n'
    '"2026-05-02T09:00:00.000000Z","2026-05-02","DEFAULT","TRADING","BUY","FUND",'
    '"Vanguard FTSE All-World","IE00BK5BQT80","44.709388","33.550000","-1500.00",'
    '"1.00","","EUR","","","","Savings plan",'
    '"22222222-2222-2222-2222-222222222222","","","",""\n'
    '"2026-05-03T09:00:00.000000Z","2026-05-03","DEFAULT","TRADING","SELL","STOCK",'
    '"Some AG","DE0007236101","5.000000","40.000000","199.00","1.00","","EUR",'
    '"","","","Sold","33333333-3333-3333-3333-333333333333","","","",""\n'
    '"2026-05-04T09:00:00.000000Z","2026-05-04","DEFAULT","CASH","CUSTOMER_INPAYMENT",'
    '"","","","","","500.000000","","","EUR","","","","Apple Pay Top up",'
    '"44444444-4444-4444-4444-444444444444","","","",""\n'
    '"2026-05-05T09:00:00.000000Z","2026-05-05","DEFAULT","CORPORATE_ACTION","DIVIDEND",'
    '"STOCK","Some AG","DE0007236101","","","12.50","","-1.90","EUR","","","",'
    '"Dividend","55555555-5555-5555-5555-555555555555","","","",""\n'
    # A type this parser has never seen. It must survive, not vanish.
    '"2026-05-06T09:00:00.000000Z","2026-05-06","DEFAULT","TRADING","SOMETHING_NEW",'
    '"STOCK","Some AG","DE0007236101","2.000000","41.000000","-82.00","","","EUR",'
    '"","","","New kind of row","66666666-6666-6666-6666-666666666666","","","",""\n'
)

NOT_A_BROKER_CSV = "name,quantity,price\nWidget,3,4.50\n"


# A record Degiro split across two lines by putting a raw newline inside
# an unquoted description. csv.reader sees two records; the second has no
# date, no amount, and the rest of the sentence.
DEGIRO_CSV_SPLIT_LINE = """Date,Time,Value date,Product,ISIN,Description,FX,Change,,Balance,,Order Id
09-04-2026,11:20,09-04-2026,,,Frais de connexion aux places boursières 2026 (New York,,EUR,"-2,50",EUR,"7131,12",
,,,,,Stock Exchange - NSY),,,,,,
"""

# The same Trade Republic export after a round trip through a spreadsheet:
# every line wrapped in one pair of quotes, inner quotes doubled.
TRADE_REPUBLIC_CSV_SPREADSHEET_MANGLED = "".join(
    '"' + line.replace('"', '""') + '"\n'
    for line in TRADE_REPUBLIC_CSV.strip().split("\n"))


# DKB Girokonto, the layout of the portal since 2023: UTF-8 with a BOM,
# semicolons, a preamble above the column header, two-digit years, and
# an amount that sometimes carries its own "€". Two identical lines on
# one day are two purchases, not one. The Vorgemerkt row is pending.
DKB_CSV_GIRO = (
    '﻿"Girokonto";"DE33 3303 3333 1112 2233 34"\n'
    '""\n'
    '"Kontostand vom 25.08.2026:";"3.210,55 €"\n'
    '""\n'
    '"Buchungsdatum";"Wertstellung";"Status";"Zahlungspflichtige*r";'
    '"Zahlungsempfänger*in";"Verwendungszweck";"Umsatztyp";"IBAN";"Betrag (€)";'
    '"Gläubiger-ID";"Mandatsreferenz";"Kundenreferenz"\n'
    '"25.08.26";"25.08.26";"Vorgemerkt";"Jane Roe";"NOCH NICHT GEBUCHT GMBH";'
    '"2026-08-25 Debitk.12 VISA Debit";"Ausgang";"DE33330333331112223334";"-19,99 €";"";"";""\n'
    '"24.08.26";"24.08.26";"Gebucht";"Jane Roe";"KAFFEEBAR AM MARKT//BERLIN/DE";'
    '"2026-08-23 Debitk.12 VISA Debit";"Ausgang";"DE33330333331112223334";"-3,40 €";"";"";""\n'
    '"24.08.26";"24.08.26";"Gebucht";"Jane Roe";"KAFFEEBAR AM MARKT//BERLIN/DE";'
    '"2026-08-23 Debitk.12 VISA Debit";"Ausgang";"DE33330333331112223334";"-3,40 €";"";"";""\n'
    '"20.08.26";"20.08.26";"Gebucht";"Jane Roe";"DKB AG";'
    '"Kreditkartenabrechnung 4998 XXXX XXXX 1234";"Ausgang";"DE33330333331112223334";'
    '"-157,90 €";"DE98ZZZ09999999999";"KK4998-1234";""\n'
    '"15.08.26";"15.08.26";"Gebucht";"Jane Roe";"Vermieter Müller";"Miete 08/2026";'
    '"Ausgang";"DE12345678901234567890";"-1.250,00 €";"";"";""\n'
    '"10.08.26";"10.08.26";"Gebucht";"Some Company GmbH";"Jane Roe";"LOHN 08/2026";'
    '"Eingang";"DE33330333331112223334";"2.345,67 €";"";"";""\n'
    '"01.08.26";"01.08.26";"Gebucht";"DKB AG";"Jane Roe";"Zinsen 07/2026";'
    '"Eingang";"DE33330333331112223334";"1,23 €";"";"";""\n'
    '"01.08.26";"01.08.26";"Gebucht";"Jane Roe";"DKB AG";"Kontoführung 07/2026";'
    '"Ausgang";"DE33330333331112223334";"-4,50 €";"";"";""\n'
)

# The same account exported two weeks later: the pending row has booked
# (with its final text), the two coffees repeat, and there is one new
# row. Only the newly booked and the new one must be added.
DKB_CSV_GIRO_OVERLAPPING = (
    '﻿"Girokonto";"DE33 3303 3333 1112 2233 34"\n'
    '""\n'
    '"Kontostand vom 08.09.2026:";"3.140,56 €"\n'
    '""\n'
    '"Buchungsdatum";"Wertstellung";"Status";"Zahlungspflichtige*r";'
    '"Zahlungsempfänger*in";"Verwendungszweck";"Umsatztyp";"IBAN";"Betrag (€)";'
    '"Gläubiger-ID";"Mandatsreferenz";"Kundenreferenz"\n'
    '"03.09.26";"03.09.26";"Gebucht";"Jane Roe";"BUCHLADEN ECKE//BERLIN/DE";'
    '"2026-09-02 Debitk.12 VISA Debit";"Ausgang";"DE33330333331112223334";"-49,99 €";"";"";""\n'
    '"26.08.26";"26.08.26";"Gebucht";"Jane Roe";"NOCH NICHT GEBUCHT GMBH//HAMBURG/DE";'
    '"2026-08-25 Debitk.12 VISA Debit";"Ausgang";"DE33330333331112223334";"-19,99 €";"";"";""\n'
    '"24.08.26";"24.08.26";"Gebucht";"Jane Roe";"KAFFEEBAR AM MARKT//BERLIN/DE";'
    '"2026-08-23 Debitk.12 VISA Debit";"Ausgang";"DE33330333331112223334";"-3,40 €";"";"";""\n'
    '"24.08.26";"24.08.26";"Gebucht";"Jane Roe";"KAFFEEBAR AM MARKT//BERLIN/DE";'
    '"2026-08-23 Debitk.12 VISA Debit";"Ausgang";"DE33330333331112223334";"-3,40 €";"";"";""\n'
    '"20.08.26";"20.08.26";"Gebucht";"Jane Roe";"DKB AG";'
    '"Kreditkartenabrechnung 4998 XXXX XXXX 1234";"Ausgang";"DE33330333331112223334";'
    '"-157,90 €";"DE98ZZZ09999999999";"KK4998-1234";""\n'
)

# The pre-2023 portal's Girokonto file: ISO-8859-1, four-digit years,
# one column for the other party, a trailing semicolon on every line.
# Bytes rather than text, because the encoding is the point.
DKB_CSV_GIRO_OLD = (
    '"Kontonummer:";"DE33330333331112223334 / Girokonto";\n'
    '\n'
    '"Von:";"01.10.2018";\n'
    '"Bis:";"20.10.2018";\n'
    '"Kontostand vom 20.10.2018:";"1.234,56 EUR";\n'
    '"Freitextsuche (im Verwendungszweck und Empfängerdaten):";"";'
    '"im Verwendungszweck und Empfängerdaten";\n'
    '"Betrag von:";"";"bis:";"";\n'
    '\n'
    '"Buchungstag";"Wertstellung";"Buchungstext";"Auftraggeber / Begünstigter";'
    '"Verwendungszweck";"Kontonummer";"BLZ";"Betrag (EUR)";"Gläubiger-ID";'
    '"Mandatsreferenz";"Kundenreferenz";\n'
    '"19.10.2018";"19.10.2018";"Lohn, Gehalt, Rente";"Some Company GmbH";'
    '"Gehalt Oktober";"DE12300301111115555666";"FOOBARFO";"2.100,00";"";"";"";\n'
    '"17.10.2018";"17.10.2018";"Lastschrift";"BÄCKEREI SCHÖN";"Brötchen";'
    '"DE9999";"BLZ";"-16,78";"DE98ZZZ01234567890";"M-1";"";\n'
).encode("iso-8859-1")

# The Visa card, current layout. "Ausgleich Kreditkarte" is the monthly
# settlement from the Girokonto; "Kartenpreis" the annual fee.
DKB_CSV_VISA = (
    '﻿"Karte";"Visa Kreditkarte 4998 •••• •••• 1234"\n'
    '""\n'
    '"Saldo vom 30.08.2026:";"-42,00 EUR"\n'
    '""\n'
    '"Belegdatum";"Wertstellung";"Status";"Beschreibung";"Umsatztyp";"Betrag";'
    '"Fremdwährungsbetrag"\n'
    '"28.08.26";"29.08.26";"Gebucht";"HOTEL BELLA VISTA ROMA";"Im Geschäft";"-42,00 €";""\n'
    '"20.08.26";"21.08.26";"Gebucht";"Ausgleich Kreditkarte gem. Abrechnung";"Lastschrift";"157,90 €";""\n'
    '"20.08.26";"20.08.26";"Gebucht";"Kartenpreis";"Entgelt";"-2,49 €";""\n'
    '"05.08.26";"06.08.26";"Gebucht";"AMAZON EU S.A.R.L.";"Online";"-155,41 €";""\n'
)

# The pre-2023 Visa file: ISO-8859-1, the balance and its date on two
# separate lines, a Ja/Nein column first, and the foreign amount last.
DKB_CSV_VISA_OLD = (
    '"Kreditkarte:";"4998********1234";\n'
    '\n'
    '"Von:";"01.10.2018";\n'
    '"Bis:";"19.10.2018";\n'
    '"Saldo:";"12345.67 EUR";\n'
    '"Datum:";"19.10.2018";\n'
    '\n'
    '"Umsatz abgerechnet und nicht im Saldo enthalten";"Wertstellung";"Belegdatum";'
    '"Beschreibung";"Betrag (EUR)";"Ursprünglicher Betrag";\n'
    '"Nein";"02.10.2018";"01.10.2018";"SOME WEBSHOP";"-5,15";"-5,95 USD";\n'
    '"Ja";"22.09.2018";"21.09.2018";"HABENZINSEN";"2,00";"";\n'
).encode("iso-8859-1")


# ─── DKB Wertpapierabrechnung PDFs ──────────────────────────────────────
# The text of each statement as a PDF text extractor returns it: one
# printed line per line, the two-column layout flattened. Layouts are
# real (they follow the anonymised corpus Portfolio Performance tests
# against); every number, name and id is invented.

DKB_PDF_KAUF = """10919 Berlin
Depotnummer 100200300
Kundennummer 9001000
Jane Roe
Auftragsnummer 611223/44.00
Frau Datum 12.03.2026
Jane Roe Rechnungsnummer W00123-0000456789/26
Musterweg 7 Umsatzsteuer-ID DE137178746
12345 Musterstadt
Wertpapier Abrechnung Kauf
Auftrag vom 11.03.2026 21:15:02 Uhr
Nominale Wertpapierbezeichnung ISIN (WKN)
Stück 2.000 EXAMPLE HOLDINGS INC. US0000000001 (EXMPL1)
REGISTERED SHARES DL -,01
Handels-/Ausführungsplatz Tradegate (gemäß Weisung)
Limit-Order
Limit 1,80 EUR
Schlusstag/-Zeit 12.03.2026 09:04:11 Auftraggeber Jane Roe
Ausführungskurs 1,75 EUR Auftragserteilung/ -ort Online-Banking
Girosammelverw. mehrere Sammelurkunden - kein Stückeausdruck -
Kurswert 3.500,00- EUR
Provision 10,00- EUR
Transaktionsentgelt Börse 2,50- EUR
Ausmachender Betrag 3.512,50- EUR
Den Gegenwert buchen wir mit Valuta 16.03.2026 zu Lasten des Kontos 12345678 (IBAN DE30 1203 0000 0012 3456 78),
BLZ 12030000 (BIC BYLADEM1001).
Die Wertpapiere schreiben wir Ihrem Depotkonto gut.
0993.03122056.0000527OR06
"""

# A fund savings-plan run: its own statement, with the same order
# number the half-year overview below repeats.
DKB_PDF_AUSGABE = """10919 Berlin
Depotnummer 100200300
Kundennummer 9001000
Jane Roe
Auftragsnummer 700111/22.00
Frau Datum 06.03.2026
Jane Roe Rechnungsnummer W00123-0000456790/26
Musterweg 7 Umsatzsteuer-ID DE137178746
12345 Musterstadt
Wertpapier Abrechnung Ausgabe Investmentfonds
Auftrag vom 04.03.2026 00:02:42 Uhr
Nominale Wertpapierbezeichnung ISIN (WKN)
Stück 2,0921 EXAMPLE MSCI WORLD U.ETF IE0000000002 (EXMPL2)
INHABER-ANTEILE I O.N.
Börse Außerbörslich (gemäß Weisung)
Schlusstag 05.03.2026 Auftraggeber Jane Roe
Ausführungskurs 95,60 EUR Auftragserteilung sonstige
Kurswert 200,00- EUR
Provision 0,49- EUR
Ausmachender Betrag 200,49- EUR
Den Gegenwert buchen wir mit Valuta 09.03.2026 zu Lasten des Kontos 12345678
(IBAN DE30 1203 0000 0012 3456 78), BLZ 12030000 (BIC BYLADEM1001).
ABR. OHNE AUSGABEAUFSCHLAG
IHR ETF-SPARPLAN NR. 1
0993.03062056.0000528OR07
"""

DKB_PDF_SPARPLAN = """10919 Berlin
Depotnummer 100200300
Kundennummer 9001000
Jane Roe
Datum 30.06.2026
Frau Vertragsbeginn 05.01.2025
Jane Roe Vertragsende b.a.w.
Musterweg 7 Sparplannummer 1
12345 Musterstadt Umsatzsteuer-ID DE137178746
Halbjahresabrechnung Sparplan
Wertpapierbezeichnung ISIN (WKN)
EXAMPLE MSCI WORLD U.ETF IE0000000002 (EXMPL2)
INHABER-ANTEILE I O.N.
Im Rahmen Ihres bestehenden Sparplans haben wir vereinbarungsgemäß nachstehende Käufe außerbörslich für Sie
durchgeführt.
Umsatzart Sparrate in Ordernummer Preis je Stück Devise Anteilsumsatz Schlusstag Valuta Zwischengewinn Steuerausgleich
EUR in EUR in Stück in EUR in EUR
Kauf 200,00 690555/11.00 92,1000 1,0000 2,1716 05.02.2026 09.02.2026 0,00 0,00
+ Provision 0,49 Summe 200,49
Kauf 200,00 700111/22.00 95,6000 1,0000 2,0921 05.03.2026 09.03.2026 0,00 0,00
+ Provision 0,49 Summe 200,49
Im Abrechnungszeitraum angelegter Betrag EUR 400,00
Im Abrechnungszeitraum erworbene Anteile Stück 4,2637
0884.06303358.0041301OF12
"""

DKB_PDF_VERKAUF = """10919 Berlin Seite 1 von 2
Depotnummer 100200300
Kundennummer 9001000
Jane Roe
Auftragsnummer 622334/55.00
Frau Datum 20.04.2026
Jane Roe Rechnungsnummer W00123-0000456791/26
Musterweg 7 Umsatzsteuer-ID DE137178746
12345 Musterstadt
Wertpapier Abrechnung Verkauf
Auftrag vom 20.04.2026 09:00:00 Uhr
Nominale Wertpapierbezeichnung ISIN (WKN)
Stück 500 EXAMPLE HOLDINGS INC. US0000000001 (EXMPL1)
REGISTERED SHARES DL -,01
Handels-/Ausführungsplatz Tradegate (gemäß Weisung)
Schlusstag/-Zeit 20.04.2026 09:05:10 Auftraggeber Jane Roe
Ausführungskurs 2,40 EUR
Kurswert 1.200,00 EUR
Provision 10,00- EUR
Ermittlung steuerrelevante Erträge
Veräußerungsgewinn 315,00 EUR
Berechnungsgrundlage für die Kapitalertragsteuer 315,00 EUR
Kapitalertragsteuer 25 % auf 315,00 EUR 78,75- EUR
Solidaritätszuschlag 5,5 % auf 78,75 EUR 4,33- EUR
Ausmachender Betrag 1.106,92+ EUR
Den Gegenwert buchen wir mit Valuta 22.04.2026 zu Gunsten des Kontos 12345678
(IBAN DE30 1203 0000 0012 3456 78), BLZ 12030000 (BIC BYLADEM1001).
0883.04202055.0000579OR07
"""

DKB_PDF_DIVIDENDE = """10919 Berlin Seite 1
Depotnummer 100200300
Kundennummer 9001000
Jane Roe
Abrechnungsnr. 86500000123
Frau Datum 15.05.2026
Jane Roe
Musterweg 7
12345 Musterstadt
Dividendengutschrift
Nominale Wertpapierbezeichnung ISIN (WKN)
Stück 1.500 EXAMPLE HOLDINGS INC. US0000000001 (EXMPL1)
REGISTERED SHARES DL -,01
Zahlbarkeitstag 15.05.2026 Dividende pro Stück 0,10 USD
Bestandsstichtag 30.04.2026 Herkunftsland USA
Ex-Tag 01.05.2026 Art der Dividende Quartalsdividende
Devisenkurs EUR / USD 1,0800
Devisenkursdatum 15.05.2026
Dividendengutschrift 150,00 USD 138,89+ EUR
Umrechnung in EUR 138,89 EUR
Einbehaltene Quellensteuer 15 % auf 150,00 USD 20,83- EUR
Anrechenbare Quellensteuer 15 % auf 138,89 EUR 20,83 EUR
Kapitalertragsteuerpflichtige Dividende 138,89 EUR
Kapitalertragsteuer 25 % auf 138,89 EUR 13,89- EUR
Solidaritätszuschlag 5,5 % auf 13,89 EUR 0,76- EUR
Ausmachender Betrag 103,41+ EUR
Lagerstelle Clearstream Banking Lux (849133 / 64003)
Den Betrag buchen wir mit Wertstellung 18.05.2026 zu Gunsten des Kontos 12345678 (IBAN DE30 1203 0000 0012 3456 78), BLZ 120 300 00 (BIC BYLADEM1001).
Bitte ggf. Rückseite beachten.
"""

DKB_PDF_VORABPAUSCHALE = """10919 Berlin Seite 1
Depotnummer 100200300
Kundennummer 9001000
Jane Roe
Abrechnungsnr. 86500000200
Frau Datum 14.01.2026
Jane Roe
Musterweg 7
12345 Musterstadt
Vorabpauschale Investmentfonds
Nominale Wertpapierbezeichnung ISIN (WKN)
Stück 40,5 EXAMPLE MSCI WORLD U.ETF IE0000000002 (EXMPL2)
INHABER-ANTEILE I O.N.
Zahlbarkeitstag 02.01.2026 Vorabpauschale pro St. 0,512000000 EUR
Bestandsstichtag 31.12.2025 mit Teilfreistellung (Aktien-
Ex-Tag 02.01.2026 fonds) 0,358400000 EUR
Geschäftsjahr 01.01.2025 - 31.12.2025 Herkunftsland Irland
Steuerpflichtige Vorabpauschale 20,74+ EUR
davon steuerfreier Anteil wg. Teilfreistellung 6,22- EUR
Kapitalertragsteuerpfl. Ertrag nach Teilfreistellung 14,52+ EUR
Berechnungsgrundlage für die Kapitalertragsteuer 14,52+ EUR
Kapitalertragsteuer 25 % auf 14,52 EUR 3,63- EUR
Solidaritätszuschlag 5,5 % auf 3,63 EUR 0,19- EUR
Ausmachender Betrag 3,82- EUR
Lagerstelle Clearstream Banking Lux (999999 / 99999)
Den Betrag buchen wir mit Wertstellung 02.01.2026 zu Lasten des Kontos 12345678 (IBAN DE30 1203 0000 0012 3456
78), BLZ 120 300 00 (BIC BYLADEM1001).
Keine Steuerbescheinigung.
"""

# A bond: nominal in euros, price in per cent.
DKB_PDF_ANLEIHE = """10919 Berlin Seite 1 von 2
Depotnummer 100200300
Kundennummer 9001000
Jane Roe
Auftragsnummer 633445/66.00
Frau Datum 25.02.2026
Wertpapier Abrechnung Kauf
Auftrag vom 24.02.2026 20:44:16 Uhr
Nominale Wertpapierbezeichnung ISIN (WKN)
EUR 2.000,00 4,25 % EXAMPLE FINANCE B.V. DE000EXMPL03 (EXMPL3)
EO-ANLEIHE 2024(29)
Börse Tradegate (gemäß Weisung)
Schlusstag/-Zeit 25.02.2026 11:02:54 Zinstermin Monat(e) 27. Juni
Ausführungskurs 97,50 % Fällig am 27.06.2029
Kurswert 1.950,00- EUR
Provision 7,50- EUR
Stückzinsen für 153 Tage per 26.02.2026 35,50- EUR
Ausmachender Betrag 1.993,00- EUR
Den Gegenwert buchen wir mit Valuta 27.02.2026 zu Lasten des Kontos 12345678 (IBAN DE30 1203 0000 0012 3456 78),
BLZ 12030000 (BIC BYLADEM1001).
"""

DKB_PDF_STORNO = """10919 Berlin
Jane Roe
Auftragsnummer 700111/22.00
Frau Datum 10.03.2026
Storno zur Wertpapier Abrechnung vom 05.03.2026
Wertpapier Abrechnung Ausgabe Investmentfonds
Nominale Wertpapierbezeichnung ISIN (WKN)
Stück 2,0921 EXAMPLE MSCI WORLD U.ETF IE0000000002 (EXMPL2)
INHABER-ANTEILE I O.N.
Ausführungskurs 95,60 EUR
Kurswert 200,00 EUR
Provision 0,49 EUR
Ausmachender Betrag 200,49 EUR
Den Gegenwert buchen wir mit Valuta 09.03.2026 zu Gunsten des Kontos 12345678
Storno, da der Ursprungsauftrag mit falscher Entgeltberechnung erfolgte.
"""

DKB_PDF_KONTOAUSZUG = """10919 Berlin
Kontoauszug Nummer 003 / 2026 vom 01.03.2026 bis 31.03.2026
Bu.Tag Wert Wir haben für Sie gebucht Belastung in EUR Gutschrift in EUR
"""


def pdf_from_text(text: str) -> bytes:
    """A real, if plain, PDF that prints the text one line at a time.

    Enough to prove the whole path — upload, `%PDF` sniff, text
    extraction, parse — without a bank's own file in the repository.
    Helvetica in WinAnsi, so the umlauts survive the round trip.
    """
    def esc(line: str) -> bytes:
        raw = line.encode("cp1252", "replace")
        return raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")

    lines = text.splitlines()
    pages = [lines[i:i + 60] for i in range(0, max(len(lines), 1), 60)]
    objects: list[bytes] = []                    # 1-based ids = index + 1
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"")                          # pages, filled in below
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                   b"/Encoding /WinAnsiEncoding >>")
    page_ids = []
    for page in pages:
        body = b"BT /F1 9 Tf 40 800 Td 12 TL " + b" T* ".join(
            b"(" + esc(l) + b") Tj" for l in page) + b" ET"
        objects.append(b"<< /Length %d >>\nstream\n" % len(body) + body + b"\nendstream")
        content_id = len(objects)
        objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                       b"/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>"
                       % content_id)
        page_ids.append(len(objects))
    objects[1] = (b"<< /Type /Pages /Count %d /Kids [" % len(page_ids)
                  + b" ".join(b"%d 0 R" % i for i in page_ids) + b"] >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += (b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objects) + 1, xref))
    return bytes(out)
