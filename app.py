import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta

st.set_page_config(page_title="KOHLER AquaSense AI", page_icon="💧", layout="wide")

@st.cache_data
def make_data():
    rng=np.random.default_rng(42)
    start=datetime(2026,9,19,6,0)
    locs=[("Block A","Floor 1","Washroom 1"),("Block A","Floor 2","Washroom 3"),
          ("Block B","Floor 1","Washroom 2"),("Block C","Floor 2","Washroom 4")]
    rows=[]
    for k,(b,f,w) in enumerate(locs):
        for i in range(96):
            ts=start+timedelta(minutes=15*i); h=ts.hour+ts.minute/60
            occ=int(max(0,rng.normal(12,4))) if 8<=h<=18 else int(max(0,rng.normal(2,1.5)))
            flow=max(0,0.15+0.18*occ+rng.normal(0,.18))
            flush=int(max(0,rng.poisson(max(.2,occ*.18))))
            health="Healthy"
            if k==1 and 14<=i<=25:
                occ=int(rng.integers(0,2)); flow=3.8+rng.normal(0,.12); flush=0
            if k==2 and 48<=i<=52:
                flow*=2.8; flush+=8
            if k==3 and 70<=i<=74:
                health="Degraded"; flow=max(0,rng.normal(.05,.03))
            rows.append([ts,b,f,w,occ,round(flow,2),flush,health])
    return pd.DataFrame(rows,columns=["timestamp","building","floor","washroom","occupancy","water_flow_lpm","flush_count","sensor_status"])

def analyze(d):
    d=d.copy()
    d["expected_flow"]=.15+.18*d["occupancy"]
    d["flow_deviation"]=d["water_flow_lpm"]-d["expected_flow"]
    X=d[["occupancy","water_flow_lpm","flush_count"]]
    d["ml_anomaly"]=IsolationForest(contamination=.08,random_state=42).fit_predict(X)==-1
    d["context_anomaly"]=(d.occupancy<=2)&(d.water_flow_lpm>=2.5)&(d.sensor_status=="Healthy")
    d["anomaly"]=d.ml_anomaly|d.context_anomaly
    d["estimated_wastage_l"]=np.where(d.anomaly,np.maximum(0,d.water_flow_lpm-d.expected_flow)*15,0)
    d["severity"]=np.where(d.context_anomaly&(d.water_flow_lpm>=3.5),"CRITICAL",
                    np.where(d.anomaly&(d.estimated_wastage_l>=30),"HIGH",
                    np.where(d.anomaly,"MEDIUM","NORMAL")))
    d["probable_cause"]=np.where(d.sensor_status!="Healthy","Sensor health issue",
                           np.where(d.context_anomaly,"Possible continuous fixture/flush-valve leak",
                           np.where(d.flush_count>np.maximum(10,d.occupancy*.8),"Unusually high flushing activity",
                           np.where(d.anomaly,"Abnormal water-use pattern","Normal"))))
    return d

df=analyze(make_data())
st.title("💧 KOHLER AquaSense AI")
st.caption("Context-aware water intelligence & predictive facility management prototype")

with st.sidebar:
    st.header("Filters")
    building=st.selectbox("Building",["All"]+sorted(df.building.unique()))
    severity=st.selectbox("Severity",["All","CRITICAL","HIGH","MEDIUM","NORMAL"])

v=df.copy()
if building!="All": v=v[v.building==building]
if severity!="All": v=v[v.severity==severity]

usage=(v.water_flow_lpm*15).sum()
waste=v.estimated_wastage_l.sum()
active=v.severity.isin(["CRITICAL","HIGH","MEDIUM"]).sum()
critical=(v.severity=="CRITICAL").sum()
a,b,c,e=st.columns(4)
a.metric("Total Water Usage",f"{usage:,.0f} L")
b.metric("Estimated Abnormal Wastage",f"{waste:,.0f} L")
c.metric("Active Alerts",int(active))
e.metric("Critical Events",int(critical))

st.subheader("Water Consumption Trend")
st.line_chart(v.groupby("timestamp").water_flow_lpm.sum())

left,right=st.columns(2)
with left:
    st.subheader("Facility Status")
    s=v.groupby(["building","floor","washroom"]).agg(
        avg_flow=("water_flow_lpm","mean"),avg_occupancy=("occupancy","mean"),
        wastage_l=("estimated_wastage_l","sum")).reset_index()
    s["status"]=np.where(s.wastage_l>100,"⚠️ Attention",np.where(s.wastage_l>0,"🟡 Monitor","🟢 Normal"))
    st.dataframe(s,use_container_width=True,hide_index=True)
with right:
    st.subheader("AI-Detected Incidents")
    inc=v[v.anomaly].sort_values("timestamp",ascending=False).head(10)
    st.dataframe(inc[["timestamp","building","floor","washroom","occupancy","water_flow_lpm","severity","estimated_wastage_l","probable_cause"]],use_container_width=True,hide_index=True)

st.subheader("🔧 Maintenance Recommendation")
high=df[df.severity.isin(["CRITICAL","HIGH"])].sort_values("estimated_wastage_l",ascending=False)
if len(high):
    r=high.iloc[0]
    st.warning(f"**{r.severity}** — {r.building} / {r.floor} / {r.washroom}\n\nProbable cause: **{r.probable_cause}**. Estimated abnormal wastage: **{r.estimated_wastage_l:.1f} L**. Recommended action: inspect fixture, flush valve and isolation valve.")
    if st.button("Create Maintenance Ticket"):
        st.success(f"Ticket KS-{int(r.timestamp.timestamp())%10000} created — Priority: {r.severity}")

st.subheader("💬 Facility Manager Assistant")
q=st.text_input("Ask a question",placeholder="Which location has the highest estimated water wastage?")
if q:
    q=q.lower()
    loc=df.groupby(["building","floor","washroom"]).estimated_wastage_l.sum().reset_index()
    if "highest" in q and "wast" in q:
        r=loc.sort_values("estimated_wastage_l",ascending=False).iloc[0]
        st.info(f"Highest estimated abnormal wastage: **{r.building} / {r.floor} / {r.washroom} — {r.estimated_wastage_l:.0f} L**.")
    elif "critical" in q or "leak" in q:
        st.info(f"The system identified **{int((df.severity=='CRITICAL').sum())} critical leak-like events**.")
    elif "saving" in q or "waste" in q:
        st.info(f"Estimated abnormal wastage: **{df.estimated_wastage_l.sum():.0f} L**.")
    else:
        st.info("Try: highest water wastage, critical leaks, or total water waste.")

st.divider()
st.caption("Prototype uses simulated telemetry. Production version can ingest live MQTT/API data and connect to a CMMS.")
