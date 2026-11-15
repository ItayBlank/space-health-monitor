# Family Connection

Family Connection is a local Earth–Mars simulation inside **Check-ins**. It uses
the existing illustrative sustained-change prompt and a preloaded acted sample.
The astronaut chooses when to play it. A check-in, a prompt, and playback are
private actions. The astronaut can also open the preloaded message from the
Family Connection panel without a prompt.

## Try the demo

1. Follow the [Check-ins setup](PRIVATE_CHECKINS.md) to provision a local crew
   account. Start the FastAPI web console on loopback and sign in to Check-ins.
2. Use **Show synthetic examples** to compare an isolated dip with a sustained
   change. Open the preloaded family message after the sustained change. The
   recording is a [CREMA-D demo clip](FAMILY_MESSAGE_DEMO.md) already served by
   the app. Synthetic ratings stay out of real history and reports.
3. In Family Connection, enable sharing with a named family recipient. Open the
   family view with the pairing code. The family view can be opened in another
   browser window and uses its own access code.
4. Pick **Mood**, **Logged sleep duration**, or both. Review the exact report and
   approve it. Mood comes from the latest real check-in. Logged sleep comes
   from the existing PVT log for the signed-in crew account and is shown as
   **Sleep unknown** when there is no usable log.
5. Set **Ground Link** to offline in the app’s Link view, refresh the Family Connection panel, and try advancing
   the Family Connection link. The report stays queued. Cancel that report,
   approve another, and bring the link back. Advance the simulation to deliver
   the approved report, then send a text reply from the family view. Advance
   delivery again and read the reply in the private astronaut inbox.
6. Turn off sharing to disconnect the family recipient and cancel any pending
   transfers.

## Data and consent

Sharing starts off. Enabling it pairs one recipient. The astronaut reviews and
approves each report before it enters the queue. Reports contain the chosen
mood rating and/or logged sleep duration. Perceived stress, check-in notes,
consult requests, and the fact that a follow-up was offered stay private.

Family Connection uses the existing simulated link’s availability and latency.
It stores messages in the private Check-ins database, apart from the general
telemetry and Mission Control packet queue. The pairing code grants access to
one family recipient’s simulated inbox. Treat it like a password. The separate
advance control runs the local simulation. No actual email, text message, or
external notification is sent. The database inherits the [local Check-ins
privacy boundary](PRIVATE_CHECKINS.md#storage-and-privacy-boundary).
