# KOHLER AquaSense AI
### AI-Powered Water Intelligence & Predictive Facility Management

Prototype for **Track 2: Commercial Smart Facility & Sustainability Manager**.

## What it does
AquaSense AI analyzes simulated facility telemetry: water flow, occupancy, flush counts and sensor health. It combines an **Isolation Forest ML anomaly detector** with **context-aware rules** to detect leak-like behavior, estimate abnormal water wastage, assign severity, recommend maintenance and demonstrate ticket creation.

### Core technical idea
A fixed threshold alone can produce false alarms. AquaSense compares observed flow with an occupancy-based expected-flow baseline. High flow with high occupancy may be normal; continuous flow with near-zero occupancy is suspicious.

## Architecture
Telemetry → Data Processing → ML + Context Rules → Incident Intelligence → Dashboard / Maintenance Ticket → Facility Assistant

## Run on Windows
Open the project folder in VS Code Terminal:
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Reproducible demo scenarios
The simulator deliberately contains:
- Continuous leak-like event: Block A / Floor 2 / Washroom 3
- Abnormal high-use event: Block B / Floor 1 / Washroom 2
- Degraded sensor event: Block C / Floor 2 / Washroom 4

## Demo flow
1. Show KPI cards.
2. Show water consumption trend.
3. Open the detected incident.
4. Explain occupancy + flow contextual detection.
5. Create a maintenance ticket.
6. Ask: "Which location has the highest estimated water wastage?"
7. Explain that simulated telemetry can be replaced by live IoT/MQTT/API data.

## Limitation
This is a proof-of-concept using simulated telemetry. Production deployment would use authenticated live IoT ingestion, time-series storage and a CMMS/facility ticketing integration.
