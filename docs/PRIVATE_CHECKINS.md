# Private mood and stress check-ins (local demo)

## Start a private local instance

From the repository root in PowerShell, choose a private data directory and
provision each crew account locally. Provisioning prompts twice for a password
and requires 12 or more characters. Existing IDs cannot be reset through this
command; no enrollment, credential reset, or user-list HTTP endpoint exists.

```powershell
$env:ASTRA_PRIVATE_DATA_DIR = "$PWD\runtime\private-checkins"
python -m astra_core.checkins provision itay
python -m astra_core.checkins provision emily
uvicorn server:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>, choose **Check-ins**, and sign in with the
provisioned crew ID and password. The web crew selector does not authenticate
this page. Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes; browser
sessions are opaque, random, HttpOnly, SameSite=Strict cookies with an eight
hour server expiry. Mutations require a same-origin `Origin` header. HTTPS
requests receive Secure cookies; the documented loopback HTTP setup uses
non-Secure cookies because TLS is not enabled.

## Ratings and trend rule

- Mood is 1 (very low) through 5 (very good); lower is worse.
- Perceived stress is 1 (none) through 5 (very high); higher is worse.
- The first five measured check-ins are the fixed personal baseline. Each
  usual range is that dimension's baseline mean ±1 rating point, clipped only
  by the natural 1–5 scale when interpreting ratings.
- A follow-up is offered when the latest three consecutive measured check-ins
  are each below the mood range, or are each above the stress range. The same
  three entries cannot update the baseline being used to evaluate them.
- The rule is illustrative, supportive, and not a diagnosis or fitness-for-duty
  decision. Missing check-ins are ignored, never counted as reassuring.

The page shows the history while fewer than five check-ins exist. Dismissing a
prompt stores its exact three-entry key, so that same triplet stays dismissed
after reload; a newer overlapping triplet may produce a new prompt.

## Evidence and scope

NASA OCHMO-STD-100.1A §6.6.2, in the [supplied Revision A PDF](https://ntrs.nasa.gov/api/citations/20240006194/downloads/OCHMO%20STD%20100%201A%2005142024.pdf), describes private in-flight psychological conferences that cover mood, performance, and crew dynamics. That linked copy contains placeholder approval dates; this project does not claim verified compliance with the current operational standard. [Inspiration4 Extended Data Figure 10](https://www.nature.com/articles/s41586-024-07648-x) reports in-flight self-ratings of mood and stress and supports those check-in fields. The 5-entry baseline, ±1-point range, and 3-consecutive-entry rule are prototype choices, not thresholds established by either source. No source dataset or external model data is imported or shipped for this feature.

## Synthetic demonstration

After sign-in, use **Show synthetic examples**. This adds two clearly marked,
separate eight-entry examples: five baseline observations plus three evaluated
observations. The isolated dip does not offer a follow-up; the sustained mood
change does. Synthetic data never enters the personal history, fixed baseline,
or consult-request store. The button replaces the prior synthetic examples for
that account when run again.

For a personal trend walkthrough, record five steady ratings (for example mood
4, stress 1), then three consecutive lower-mood (for example mood 2, stress 1)
or higher-stress (for example mood 4, stress 3) ratings. An isolated change
does not trigger the rule.

## Consult requests

No entries are shared by default. Select specific history rows, open the
request panel, inspect its exact values and the named recipient **Flight
surgeon (local demo)**, then check explicit consent. The server verifies every
selected ID belongs to the signed-in owner and records only those selected IDs
with `locally_recorded_not_delivered` status. No message is sent, and synthetic
entries cannot be selected.

## Storage and privacy boundary

The SQLite database lives under `ASTRA_PRIVATE_DATA_DIR` (default:
`~/.astra-core/private/checkins.sqlite3`). SQLite transactions and WAL mode
provide atomic updates across threads/processes; the containing directory is
restricted to the current OS account where supported. The database is not
encrypted. The computer owner, OS administrator, server operator, or anyone
with filesystem access can read private records and credential hashes. This
local demonstration is not a production confidential care system; bind to
loopback and do not expose it to a network. Check-ins are not included in
readiness, companion context, telemetry snapshots, or downlink.

## Tests

```powershell
python -m pytest -q tests/test_private_checkins_api.py
```

The tests cover unauthenticated access, wrong credentials, owner isolation,
expiry and logout, baseline establishment, isolated versus sustained and
dimension-mixed trends, dismissal behavior, explicit consent, selected-entry
ownership, and synthetic-data separation.
