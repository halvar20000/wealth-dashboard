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
