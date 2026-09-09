"""Bank connections.

One module per provider. Enable Banking is the first because it covers
most of the EEA with one registration; a second provider would sit
beside it and expose the same three verbs the app uses — list banks,
begin authorisation, sync an account.
"""

from . import enablebanking  # noqa: F401
