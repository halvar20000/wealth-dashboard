# Privacy — the Wealth phone apps

Both the Android and the iOS app talk to one server: the Wealth Dashboard you paired it
with, which is yours. There is no account to make, no telemetry, no
analytics, no advertising identifier, no crash reporter, and no server
of ours in the middle — there is no "ours".

## What the app holds

On the phone, in Android's encrypted preferences
(`EncryptedSharedPreferences`, keyed by the phone's hardware keystore):

- the address of your dashboard and the token it issued when you paired,
- the last figures it sent, so a cold start and the home-screen widget
  show something without waiting for a network,
- the decisions you took in Triage that have not reached the dashboard
  yet.

Nothing else is stored, and none of it leaves the phone except back to
your own dashboard. **Forget this dashboard** in Settings removes all of
it.

## What the app sends

Only to the address you paired with:

- the token, on each request, as a bearer header,
- what you decided in Triage (a category, a person, a rule to remember),
- a statement you share into the app, when you share one.

Your bank credentials are never involved: this app never speaks to a
bank. The dashboard does that, on your own network.

## Permissions

- **Internet** and **network state** — to reach your dashboard.
- **Notifications** (Android 13+) — only if you switch on *Watch in the
  background*, and only for a low balance ahead, a bank link that has
  stopped, or a queue that has grown.
- Biometric — if you switch on *Ask to unlock*; the check happens on the
  phone and nothing about it is sent anywhere.

## Backups

`allowBackup` is off. The token and the figures are not in Google's
cloud backup of the phone.

## Children

The app is not directed at children and collects nothing from anybody.

## Contact

Issues and questions: <https://github.com/halvar20000/wealth-dashboard/issues>

*This is the copy Google Play and the App Store link to. It is kept in
the dashboard's repository because that one is public; the apps' own
repository is not.*
