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
    # `shares` and `price` are filled on a dividend row: the position
    # it was paid on and the amount per share. Not a trade.
    '"STOCK","Some AG","DE0007236101","2.000000","6.250000","12.50","","-1.90","EUR","","","",'
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


# ─── Swissquote, Yuh, Crédit Agricole (Suisse) ─────────────────────────
# The shapes of the real documents as pypdf reads them, with made-up
# names and numbers. The old layout carries page furniture in the middle
# of the table, which the parser must step over.

SWISSQUOTE_KONTOAUSZUG = """Dieser Transaktionsbeleg sowie die aufgeführte Transaktion unterliegen unseren Allgemeinen Geschäftsbedingungen und Depotreglement.
Swissquote Bank AG, 33 chemin de la CrØtaux, CH-1196 Gland
Seite 1 / 3
Herrn Max Muster
IBAN CH67 0878 1000 3163 2010 0
Kunde 3163201
Kontoart TRADING
Ihr Kontoauszug
Kontoauszug vom 01.05.2026 bis 31.05.2026
Dokument erstellt am 01.06.2026
Anfangssaldo 22’443.21 CHF
Endsaldo 21’295.65 CHF
Kontoauszug in CHF
Saldo per 01.05.2026 22’443.21 CHF
Total Belastung 8’067.56 CHF
Total Gutschrift 6’920.00 CHF
Saldo per 31.05.2026 21’295.65 CHF
DATUM INFORMATION REFERENZ BELASTUNG GUTSCHRIFT VALUTA-DATUM SALDO (CHF) 
01.05.2026
 Anfangsbestand 22’443.21
04.05.2026
 Zahlung von
MAX MUSTER
RUE DU RHIN 1
68680 KEMBS France
CH6508243119173342001
1090000001 6’900.00 04.05.2026 29’343.21
05.05.2026
 Kauf
SS SPDR MSCI All County World
(ACWI)
Anzahl: 30
Preis: CHF 228.00
Betrag: CHF 6’840.00
Kommission: CHF 9.85
Taxen: CHF 10.26
Handelsplatz: SIX Swiss Exchange
ISIN: IE00B44Z5B48
1090000002 6’862.64 07.05.2026 22’480.57
06.05.2026
 Zahlung an
Erika Beispiel
FR7610278030710002071330218
CREDIT MUTUEL
Transfer
1090000003 102.00 06.05.2026 22’378.57
07.05.2026
 Automatisierter Währungstausch
CHF - EUR
1 CHF = 1.08173 EUR
1090000004 99.84 07.05.2026 22’278.73
Dokument erstellt am 01.06.2026
Vom 01.05.2026 bis 31.05.2026
Herrn Max Muster
IBAN : CH67 0878 1000 3163 2010 0
Dieser Transaktionsbeleg sowie die aufgeführte Transaktion unterliegen unseren Allgemeinen Geschäftsbedingungen und Depotreglement.
Swissquote Bank AG, 33 chemin de la CrØtaux, CH-1196 Gland
Seite 2 / 3
DATUM INFORMATION REFERENZ BELASTUNG GUTSCHRIFT VALUTA-DATUM SALDO (CHF) 
11.05.2026
 Zahlung per Debitkarte
xxxx 5861 -
CFF GenŁve Cornavin WC
Pl. de Cornavin 1
1201 GenŁve
1090000005 1.50 09.05.2026 22’277.23
12.05.2026
 Dividende
iSh Cor SPI CH CHF D (CHSPI)
Anzahl: 12.631
Betrag: CHF 9.85
Taxen: CHF 3.45
Total: CHF 6.40
1090000006 6.40 12.05.2026 22’283.63
31.05.2026
 Depotgebühren 20.00 31.05.2026 22’263.63
31.05.2026
 Transfer 1090000007 6.90 31.05.2026 22’256.73
31.05.2026
 Zahlung an
Max Muster
CH3608781000317056500
1090000008 961.08 31.05.2026 21’295.65
31.05.2026
 Schlussbilanz 21’295.65
Kontoauszug in EUR
Saldo per 01.05.2026 0.00 EUR
Total Belastung 108.00 EUR
Total Gutschrift 108.00 EUR
Saldo per 31.05.2026 0.00 EUR
DATUM INFORMATION REFERENZ BELASTUNG GUTSCHRIFT VALUTA-DATUM SALDO (EUR) 
01.05.2026
 Anfangsbestand 0.00
07.05.2026
 Zahlung per Debitkarte
xxxx 5861 -
CLAUDE.AI SUBSCRIPTION
D02 H210 DUBLIN
1090000009 108.00 07.05.2026 -108.00
07.05.2026
 Automatisierter Währungstausch
CHF - EUR
1 EUR = 0.92444 CHF
1090000004 108.00 07.05.2026 0.00
31.05.2026
 Schlussbilanz 0.00
Vertriebsentschädigungen
Im Rahmen des Vertriebs von Finanzprodukten erhält Swissquote Bank AG Vertriebsentschädigungen.
"""

SWISSQUOTE_TRANSAKTIONSAUFSTELLUNG = """24.07.2026 bis 24.08.2026 - Erstellt am 25.08.2026
Referenzwährung
Anfangssaldo
Endsaldo
18’957.33 CHF
13’844.10 CHF
Max Muster
Kunde
IBAN
SWIFT
CH67 0878 1000 3163 2010 0
3163201
SWQBCHZZ XXX
Transaktionsaufstellung
Swissquote Bank AG, 33 chemin de la Crétaux, CH-1196 Gland - Customer Care : +41 44 825 88 88 1
Alle
 / 2
Transaktionsaufstellung in CHF Max Muster
IBAN: CH67 0878 1000 3163 2010 0 (CHF)24.07.2026 bis 24.08.2026 - Erstellt am 25.08.2026
Anfangssaldo
18’957.33 CHF
Einzahlung
11’616.00 CHF
Auszahlung
16’729.23 CHF
Endsaldo
13’844.10 CHF
Datum Referenz Information Gebühren und
Steuern Betrag Valuta-Datum Saldo
24.07.2026 1142225922 Eingehende Zahlung
BEISPIEL AG
WURMISWEG 576 4303 KAISERAUGST
IBAN: CH1287801001000300007
+11’616.00 CHF 24.07.2026 30’573.33 CHF
27.07.2026 1143867441 Einzahlung für Max Muster
IBAN: FR7617206005719302143281247
BIC/SWIFT: AGRIFRPP872
2 CHF -1’428.00 CHF 27.07.2026 29’145.33 CHF
28.07.2026 1144621900 Kartenzahlung - mit der Endnummer 5861
Digitec Galaxus AG
Steinentorberg 20, Schweiz
-444.90 CHF 28.07.2026 28’700.43 CHF
04.08.2026 1148865375 Kartengebühren -6.90 CHF 04.08.2026 28’693.53 CHF
10.08.2026 1152885176 Automatisierte Überweisung CHF an EUR
Wechselkurs: 1 CHF = 1.069284 EUR
Betrag: 56.42 EUR
-53.28 CHF 10.08.2026 28’640.25 CHF
21.08.2026 1150239202 Einzahlung für Helsana Versicherungen AG
IBAN: CH0230000002319545324
Referenz: 100686290826006038876100001
-14’796.15 CHF 21.08.2026 13’844.10 CHF
Swissquote Bank AG, 33 chemin de la Crétaux, CH-1196 Gland - Customer Care : +41 44 825 88 88 2
Alle
 / 2
Transaktionsaufstellung in EUR Max Muster
IBAN: CH67 0878 1000 3163 2010 0 (CHF)24.07.2026 bis 24.08.2026 - Erstellt am 25.08.2026
Anfangssaldo
0.00 EUR
Einzahlung
56.42 EUR
Auszahlung
56.42 EUR
Endsaldo
0.00 EUR
Datum Referenz Information Gebühren und
Steuern Betrag Valuta-Datum Saldo
10.08.2026 1152345178 Kartenzahlung - mit der Endnummer 5861
pay.amazon.com
5 rue plaetis, Luxemburg
-56.42 EUR 10.08.2026 -56.42 EUR
10.08.2026 1152885176 Automatisierte Überweisung CHF an EUR
Wechselkurs: 1 CHF = 1.069284 EUR
Betrag: 53.28 CHF
+56.42 EUR 10.08.2026 0.00 EUR
Vertriebsentschädigungen
Die Swissquote Bank AG nimmt Vertriebsentschädigungen entgegen.
"""

YUH_KONTOAUSZUG = """Die vorliegende Benachrichtigung sowie die Transaktionen unterliegen unseren Allgemeinen Geschäftsbedingungen für Yuh-Konten und allen sonstigen Bedingungen, die zwischen
dir und Yuh Ltd und/oder Swissquote Bank Ltd bezüglich deines Yuh-Kontos gelten.
Swissquote Bank Ltd, Chemin de la CrØtaux 33, CH-1196 | Gland
© 2022 Yuh Ltd Seite 1 / 2
Dein Kontoauszug
Kontoauszug vom 01.11.2025 bis 30.11.2025
Dokument erstellt am 01.12.2025
Yuh account
IBAN CH71 0878 1000 2892 0620 0
Kunde 2892062
Anfangssaldo 994.25 CHF
Endsaldo 81.10 CHF
Kontoauszug in CHF
Saldo per 01.11.2025 994.25 CHF
Total Belastung 1’913.15 CHF
Total Gutschrift 1’000.00 CHF
Saldo per 30.11.2025 81.10 CHF
DATUM INFORMATION REFERENZ BELASTUNG GUTSCHRIFT VALUTA-DATUM SALDO (CHF) 
01.11.2025
 Anfangsbestand 994.25
07.11.2025
 Kauf
LOGITECH N (LOGN)
Anzahl: 2.5741
Preis: CHF 97.12
Betrag: CHF 250.00
Kommission: CHF 1.25
Taxen: CHF 0.20
Handelsplatz: SIX Swiss Exchange
ISIN: CH0025751329
972551649 251.45 10.11.2025 742.80
27.11.2025
 Zahlung von
MAX MUSTER
CH6508243119173342001
984637474 1’000.00 27.11.2025 1’742.80
28.11.2025
 Kauf
UBSETF SMIM CHF dis (SMMCHA)
Anzahl: 3.3933
Preis: CHF 294.70
Betrag: CHF 1’000.00
Kommission: CHF 5.00
Taxen: CHF 0.75
Handelsplatz: SIX Swiss Exchange
ISIN: CH0111762537
985446144 1’005.75 01.12.2025 737.05
28.11.2025
 Kauf
UBSETF SMIM CHF dis (SMMCHA)
Anzahl: 2.2198
Preis: CHF 293.80
Betrag: CHF 652.20
Kommission: CHF 3.25
Taxen: CHF 0.50
Handelsplatz: SIX Swiss Exchange
ISIN: CH0111762537
985501567 655.95 01.12.2025 81.10
30.11.2025
 Schlussbilanz 81.10
Vertriebsentschädigungen
"""

SWISSQUOTE_BELEG = """TRANSAKTIONSBELEG
Kunde: 3163201 - TRADING
IBAN: CH6708781000316320100
Gland, 05.05.2026
Swissquote Bank AG, 33 chemin de la Crétaux, CH-1196 Gland
Unsere Referenz: 1090000002 
Herrn Max Muster
Börsentransaktion: Kauf
Total CHF 6'840.00
Kommission Swissquote Bank AG CHF 9.85
Abgabe (Eidg. Stempelsteuer) CHF 10.26
Börsengebühren CHF 2.53
Zu Ihren Lasten CHF 6'862.64
Titel Börse
SPDR MSCI ACWI ISIN: IE00B44Z5B48
NKN: 12930745
SIX Swiss Exchange 
Gemäss Ihrem Kaufauftrag vom 05.05.2026 haben wir folgende Transaktionen vorgenommen:
Betrag belastet auf Kontonummer  316320100, Valutadatum 07.05.2026
Anzahl Preis Betrag
30 228 CHF 6'840.00
Vielen Dank für Ihren Auftrag.
"""

SWISSQUOTE_BELEG_VERKAUF = """TRANSAKTIONSBELEG
Kunde: 3170565 - Invest Easy
Gland, 12.06.2026
Swissquote Bank AG, 33 chemin de la Crétaux, CH-1196 Gland
Unsere Referenz: 1100000001 
Börsentransaktion: Verkauf
Total CHF 1'013.30
Börsengebühren CHF 0.07
Zu Ihren Gunsten CHF 1'013.23
Titel Börse
Ambitious Portfolio IndexIndex ISIN: CH1236310558
SIX Swiss Exchange 
Gemäss Ihrem Verkaufsauftrag vom 12.06.2026 haben wir folgende Transaktionen vorgenommen:
Anzahl Preis Betrag
28 36.19 CHF 1'013.32
"""

CA_SWITZERLAND_CSV = (
    "Transaktionsdatum;Valutadatum;Auftragsnummer;Text;Belastungsbetrag (CHF);Gutschriftsbetrag (CHF);Saldo (CHF)\n"
    "24.08.2026;24.08.2026;236765220;Paiement en faveur de: Swissquote Bank SA;3700.00;;11.26\n"
    "21.08.2026;21.08.2026;236618546;\"Schweizerische Stiftung, Aeschengraben 26, 4051 Basel, CH\";;3714.80;3711.26\n"
    "30.07.2026;31.07.2026;234080873;Refund discounted fee;;3.00;-3.54\n"
    "24.07.2026;31.07.2026;233428503;Basic Fee - Debit Order: MUSTER MAX;15.00;;-6.54\n"
    "23.07.2026;23.07.2026;233171117;Instant Payment in favour of: Max Muster;3705.00;;8.46\n"
    "30.06.2026;30.06.2026;230690990;31.03.26-30.06.26;0.15;;-1.34\n"
    "31.12.2025;31.12.2025;210924780;31.12.24-31.12.25;;98.57;49387.41\n"
    "15.12.2025;15.12.2025;209467357;Paiement en faveur de: Café Zürich Müller;300.00;;49288.84\n"
).encode("cp1252")


# Finary's crypto export: one row per event, what was received and what
# was sent. A buy, a swap (coin for coin), a withdrawal to the user's own
# wallet, and a fiat deposit. The ids are Finary's UUIDs.
FINARY_CSV = """type,date,timezone,received_amount,received_currency,sent_amount,sent_currency,fee_amount,fee_currency,description,address,transaction_hash,external_id,eur_value
Deposit,2026-01-30T10:00:00.000000000Z,GMT,50.00,EUR,,,,,Deposit,,,019c0000-0000-0000-0000-000000000000,50.00
Trade,2026-01-31T11:00:30.017657763Z,GMT,0.00035318,BTC,24.75,EUR,0.25,EUR,Buy,,,019c13b6-064f-72a1-8cdf-a82bc96247f1,25.00
Trade,2026-01-31T11:00:36.810215685Z,GMT,0.011072,ETH,24.75,EUR,0.25,EUR,Buy,,,019c13b6-064f-72a1-8cdf-a835fe8c6484,25.00
Trade,2026-05-19T12:38:59.608092187Z,GMT,0.03500598,BTC,0.011072,ETH,0.00035006,BTC,Swap,,,019e403f-004b-7541-a2ee-9c51ef7a6851,2338.83
Withdrawal,2026-05-22T13:20:01.621331956Z,GMT,,,0.03535916,BTC,0.25,EUR,Withdrawal through Bitcoin network,3NxV7W9e7wnMgMJ2URMA8iRhhuttmEfHha,802b51a9,019e4fc1-7872-7f70-b422-a5d680e74433,
"""


# ─── Payslips ────────────────────────────────────────────────────────
# Two Swiss payslip layouts, as pypdf reads them. Every name and figure
# is invented; the shapes are the real ones — the SAP sheet with its
# wage codes and employer block, and the small employer's sheet whose
# text arrives with the spaces gone and an O where a zero was printed.

PAYSLIP_SAP = """Bei Fragen wählen Sie bitte die Nr 00800 12388 888.
Herr Max Muster               
1 Musterweg                   
CH-4000 BASEL                 
Muster Chemie AGFirma
Personal-Nr. 40099999
SV Nummer
Besch.grad
756.0000.0000.00
100,00
Monat März 2026
Valuta 25.03.2026
Seiten Nr. 1 /  1
Lohn
Einkommen
Retro Beschreibung Basis Ansatz Betrag
0110 Monatsgehalt (12)              10.000,00 
5035 Familienzulage                    250,00 
/101 BRUTTO        10.250,00 
/411 AHV-Beitrag                    10.250,00 5,300 %     543,25-
/420 ALV-Beitrag                    10.250,00  1,10  %     112,75-
6801 PF1 Beitrag AN                    300,00-
6805 PF1 Risiko Beitrag AN              80,00-
6819 KSP Beitrag AN                    120,00-
/260 Sozialabzüge         1.156,00-
/550 NETTO         9.094,00 
/310 Quellensteuer                 10.250,00  12,00 %    1.230,00-
6001 Kantine                            40,00-
/110 Bezüge/Abzüge               1.270,00-
Auszahlung             7.824,00 
Sonderzahlungen / Abzüge
Beschreibung Betrag
Arbeitgeberbeiträge
Beschreibung Betrag
FAK-Beitrag AG Kassenreg.     110,00 
AHV-Prämie AG-Anteil              543,25 
ALV / AG-Anteil                   112,75 
PF1 Beitrag AG                    900,00 
PF1 Risiko Beitrag AG            160,00 
KSP Beitrag AG                    120,00 
Bankverbindung
Bankschlüssel Bankname Konto Banküberweisung
8243 Musterbank AG CH0000000000000000000            7.824,00  CHF
Mitteilung
"""

PAYSLIP_LOHNABRECHNUNG = """MusterstiftungfürForschung
Musterstrasse1
4000Basel
Personalnummer:7
Soz.Vers.Nr.:756.0000.0000.00
Datum:11.Dezember2025
LohnabrechnungDezember2025
ErikaMuster
1Musterweg
4000Basel
Bezeichnung
Auszahlung
MengeAnsatzBetrag
Auszahlungam15.12.2025
Fr.5’421.50aufIBANCH0000000000000000000-CHF,Musterbank
Monatslohn4’000.00
13.Monatslohn2’000.00
Gratifikation1’OOO.OO
Bruttolohn7’000.OO
AHV-Beitrag7’000.005.30%-371.00
ALV-Beitrag7’000.001.10%-77.00
BVG-Beitrag-130.50
Nettolohn6’421.50
6’421.50
"""

# A third layout no parser here was written for — a French bulletin
# with its retenues printed positive and French numbers — for the
# mapper: the user says which line is which, once.
PAYSLIP_BULLETIN = """BULLETIN DE PAIE
Période : Mars 2026        Date de paiement : 31/03/2026
Employeur : Exemple SAS            Salarié : Jean Dupont
Salaire de base                     3 500,00
Prime d'ancienneté                    120,00
Salaire brut                        3 620,00
Sécurité sociale maladie   3 620,00   0,75 %     27,15
Assurance chômage          3 620,00   2,40 %     86,88
Retraite complémentaire AGIRC-ARRCO  3 620,00  3,15 %   114,03
CSG déductible                                   248,00
Prélèvement à la source    12,00 %               350,00
Mutuelle                                          40,00
Net à payer                         2 753,94
Retraite part patronale                          250,00
"""
