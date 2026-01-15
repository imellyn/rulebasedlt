# app.py
import streamlit as st
import json
from typing import Dict, List, Any, Optional

st.set_page_config(
    page_title="Smart Home AC Controller",
    page_icon="❄️",
    layout="centered"
)

st.title("❄️ Smart Home Air Conditioner Rule-Based Controller")
st.markdown("Rule-based expert system for transparent & adjustable AC control")


DEFAULT_RULES = [
    {
        "name": "Windows open",
        "priority": 100,
        "conditions": [
            ["windows_open", "==", True]
        ],
        "action": {
            "mode": "OFF",
            "fan_speed": "LOW",
            "setpoint": None,
            "reason": "Windows are open → turn AC off"
        }
    },
    {
        "name": "Too cold",
        "priority": 95,
        "conditions": [
            ["temperature", "<=", 22]
        ],
        "action": {
            "mode": "OFF",
            "fan_speed": "LOW",
            "setpoint": None,
            "reason": "Already too cold → turn AC off"
        }
    },
    {
        "name": "No one home → eco mode",
        "priority": 90,
        "conditions": [
            ["occupancy", "==", "EMPTY"],
            ["temperature", ">=", 24]
        ],
        "action": {
            "mode": "ECO",
            "fan_speed": "LOW",
            "setpoint": 27,
            "reason": "Home empty → eco mode to save energy"
        }
    },
    {
        "name": "Hot & humid (occupied)",
        "priority": 80,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 30],
            ["humidity", ">=", 70]
        ],
        "action": {
            "mode": "COOL",
            "fan_speed": "HIGH",
            "setpoint": 23,
            "reason": "Hot and very humid → strong cooling"
        }
    },
    {
        "name": "Night sleep mode",
        "priority": 75,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["time_of_day", "==", "NIGHT"],
            ["temperature", ">=", 26]
        ],
        "action": {
            "mode": "SLEEP",
            "fan_speed": "LOW",
            "setpoint": 26,
            "reason": "Night time → sleep mode for comfort"
        }
    },
    {
        "name": "Hot (occupied)",
        "priority": 70,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 28]
        ],
        "action": {
            "mode": "COOL",
            "fan_speed": "MEDIUM",
            "setpoint": 24,
            "reason": "High temperature → cooling"
        }
    },
    {
        "name": "Slightly warm (occupied)",
        "priority": 60,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 26],
            ["temperature", "<", 28]
        ],
        "action": {
            "mode": "COOL",
            "fan_speed": "LOW",
            "setpoint": 25,
            "reason": "Slightly warm → gentle cooling"
        }
    }
]

st.sidebar.header("Rule Configuration")
rules_json = st.sidebar.text_area(
    "Edit / View Rules (JSON format)",
    value=json.dumps(DEFAULT_RULES, indent=2),
    height=480
)

try:
    rules = json.loads(rules_json)
    st.sidebar.success("Rules loaded successfully")
except json.JSONDecodeError as e:
    st.sidebar.error(f"JSON Error: {e}")
    rules = []

# Main Input Area
st.header("Current Home Conditions")

col1, col2 = st.columns(2)

with col1:
    temperature = st.number_input("Temperature (°C)", 15.0, 38.0, 22.0, 0.5)
    humidity = st.number_input("Relative Humidity (%)", 20, 95, 46, 1)
    occupancy = st.radio("Occupancy Status", ["OCCUPIED", "EMPTY"], index=0)

with col2:
    time_of_day = st.selectbox("Time of Day", ["MORNING", "AFTERNOON", "EVENING", "NIGHT"])
    windows_open = st.checkbox("Windows Open", value=False)

# Facts dictionary
facts = {
    "temperature": float(temperature),
    "humidity": float(humidity),
    "occupancy": occupancy,
    "time_of_day": time_of_day,
    "windows_open": bool(windows_open)
}

#Rule Engine
def evaluate_condition(cond: List[Any], facts: Dict) -> bool:
    if len(cond) != 3:
        return False
    
    field, operator, value = cond
    
    if field not in facts:
        return False
    
    actual = facts[field]
    
    # Handle different value types safely
    if isinstance(value, (int, float)) and isinstance(actual, (int, float)):
        actual_val = float(actual)
        rule_val = float(value)
    else:
        actual_val = str(actual).upper()
        rule_val = str(value).upper()
    
    if operator == "==": return actual_val == rule_val
    if operator == "!=": return actual_val != rule_val
    if operator == ">=": return actual_val >= rule_val
    if operator == "<=": return actual_val <= rule_val
    if operator == ">":  return actual_val > rule_val
    if operator == "<":  return actual_val < rule_val
    
    return False


def run_rule_engine(rules: List[Dict], facts: Dict) -> Optional[Dict]:
    # Sort by priority (highest first)
    sorted_rules = sorted(rules, key=lambda r: r.get("priority", 0), reverse=True)
    
    for rule in sorted_rules:
        conditions = rule.get("conditions", [])
        if all(evaluate_condition(c, facts) for c in conditions):
            return {
                "rule_name": rule.get("name", "Unnamed Rule"),
                "action": rule.get("action", {}),
                "priority": rule.get("priority", 0)
            }
    return None


if st.button("Determine AC Settings", type="primary"):
    if not rules:
        st.error("No valid rules loaded. Please correct the JSON in sidebar.")
    else:
        result = run_rule_engine(rules, facts)
        
        st.markdown("---")
        
        if result:
            action = result["action"]
            st.subheader("Decision Made by Rule Engine")
            
            mode = action.get("mode", "—")
            fan = action.get("fan_speed", "—")
            setpoint = action.get("setpoint", "—")
            reason = action.get("reason", "No specific reason provided")
            
            cols = st.columns([1,1,1,2])
            cols[0].metric("AC Mode", mode)
            cols[1].metric("Fan Speed", fan)
            cols[2].metric("Setpoint", f"{setpoint}°C" if setpoint else "—")
            
            st.info(f"**Rule Triggered:** {result['rule_name']} (priority {result['priority']})")
            st.success(f"**Reason:** {reason}")
            
        else:
            st.warning("No rule matched the current conditions")
            st.info("Default behavior: AC remains OFF / unchanged")
        
        # Show current facts
        with st.expander("Current Home Facts"):
            st.json(facts)
