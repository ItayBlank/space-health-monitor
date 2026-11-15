# Demonstration guide

## Current web walkthrough

Launch the web console using [README](../README.md), then open localhost:8000.
Use the synthetic scenarios for a repeatable walkthrough.

1. **Glance / Actions:** select crew and a scenario. Distinguish synthetic scenario
   telemetry from research replay and explain that recommendations are illustrative.
2. **Heart / RadLab:** show physiological replay and modeled exposure with cabin
   schedules. Describe derived estimates and storm multipliers as model outputs.
3. **Sensors.** Show the calibrated vision flow. In the [three-minute PVT](PVT.md),
   compare **Short sleep**, **Already tested**, and **Missing sleep log**. The
   recommendation supports crew review.
4. **Link:** inspect a locally queued report and simulated delivery. There is no
   real ground-control delivery acknowledgement.
5. **HAL.** Open Family Archive and play the [family-message demo](FAMILY_MESSAGE_DEMO.md).
   For live speech, install the local voice models and enable the microphone.
6. **Check-ins.** Follow the [local setup](PRIVATE_CHECKINS.md), sign in, and use
   **Show synthetic examples** to compare an isolated dip with sustained change.

## Legacy desktop three-minute demonstration

The walkthrough below applies to the retained PySide6 app (`main.py`). Its page
names and voice placeholders must not be presented as web behavior.

## 0:00–0:25 — One shared health picture

Open **Crew overview**. Show all six crew members, their activity badges, three main vitals and connected sensor counts. Explain that the supplied ten-minute recording is being replayed at 1 Hz, and that the application is running locally.

Suggested line: “HAL2030 puts the crew's current health picture in one place, even when Earth is unavailable.”

## 0:25–0:55 — A physiological event

Choose **00:40 · Anton: oxygen alert** from the scenario selector and pause. Point to the red ring, enlarged portrait and global alert. Click Anton's enlarged portrait to open the recommended-action card. The card asks the crew medical officer to verify saturation, assess breathing and review cabin conditions, including oxygen only under the approved procedure.

Open **Crew detail** from that card. Show the live values, illustrative ECG/respiration/EEG and trend plots. Explain which parts come from the CSV and which traces are synthetic illustrations.

## 0:55–1:20 — Missing signal is a different problem

Choose **02:00 · Itay: oximeter signal lost**. Open **Sensor network**, filter for Itay or missing signal, and point to the amber state and `—` saturation. The application reports a missing observation without pretending the astronaut's physiology is normal or abnormal.

Choose **03:05 · Emily: exercise** to show that an expected increase during activity does not create a false resting-rate emergency.

## 1:20–1:55 — Communication with delay

Open **Mission control**. Use the 3-second delay and send a snapshot. Inspect its JSON and watch the local simulated receipt.

Turn off **Ground link available**, send another packet and show its queued state. Restore the link and show it resume. Select the 22-minute scenario to illustrate why the crew needs onboard decision support. State that this demonstration uses a local queue and no NASA endpoint.

## 1:55–2:35 — Personal onboard companion

Open Anton's **HAL2030** session. Click **I miss home** or type a message. Switch to another astronaut and back to demonstrate separate histories. Start the voice demo to show listening/transcript/reply interface states.

Select **Family archive · simulated**. The interface marks the replies as generated simulations rather than real family contact. Open the model/archive setup previews to show where future offline inference and approved archives would connect. These engines are placeholders in this version.

## 2:35–3:00 — Recovery and implementation

Choose **08:50 · Crew recovered**. Return to the overview and show the green status rings. Briefly point out that acquisition, rules, transmission and GUI pages are separate Python modules, so hardware and an offline model can be integrated without rewriting the whole interface.

Suggested close: “The prototype demonstrates the complete interaction loop: observe, distinguish missing data from an abnormal signal, review an action, keep a local record, and forward it when the link permits.”
