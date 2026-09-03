import pandas as pd
import numpy as np
import sqlite3
import pickle
import os
import re
from io import StringIO
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

script_dir = os.path.dirname(os.path.abspath(__file__))
local_file = os.path.join(script_dir, "standings.html")

print(f"Targeting local file path: {local_file}")

if os.path.exists(local_file):
    # Successfully loads local html file bypassing network/firewall hurdles
    tables = pd.read_html(local_file)
    print("Successfully loaded standings from local 'standings.html'!")
else:
    # Scrape fallback with headers as defined in Example_pd_html
    import requests
    print("Local standings.html not found in script folder. Attempting live scrape...")
    url = "https://www.espn.com/nfl/standings"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))

afc_names = tables[0]
afc_stats = tables[1]
nfc_names = tables[2]
nfc_stats = tables[3]

afc_stats.columns = afc_stats.iloc[0]
afc_stats = afc_stats[1:].reset_index(drop=True)

nfc_stats.columns = nfc_stats.iloc[0]
nfc_stats = nfc_stats[1:].reset_index(drop=True)

afc = pd.concat([afc_names, afc_stats], axis=1)
nfc = pd.concat([nfc_names, nfc_stats], axis=1)

df = pd.concat([afc, nfc], ignore_index=True)

df.rename(columns={df.columns[0]: 'Tm'}, inplace=True)

def clean_team_name(name):
    if not isinstance(name, str):
        return name
    name = re.sub(r'^[a-z]\s*-\s*', '', name, flags=re.IGNORECASE)  # Clinching prefix (e.g. x - )
    name = re.sub(r'^\d+\s*', '', name)                           # Seeding prefix
    # Strip trailing uppercase abbreviation (e.g., 'Buffalo BillsBUF' -> 'Buffalo Bills')
    name = re.sub(r'([a-z]+)([A-Z]{2,4})$', r'\1', name)
    return name.strip()

df['Tm'] = df['Tm'].apply(clean_team_name)

df['PF'] = pd.to_numeric(df['PF'], errors='coerce').astype(float)
df['PA'] = pd.to_numeric(df['PA'], errors='coerce').astype(float)
df['PD'] = df['PF'] - df['PA']

df = df.dropna(subset=['PF', 'PA']).reset_index(drop=True)

if 'SoS' not in df.columns:
    df['SoS'] = 0.0
else:
    df['SoS'] = pd.to_numeric(df['SoS'], errors='coerce').fillna(0.0).astype(float)

df['W'] = pd.to_numeric(df['W'], errors='coerce').fillna(0).astype(int)
df['L'] = pd.to_numeric(df['L'], errors='coerce').fillna(0).astype(int)

df['Win_Percentage'] = df['W'] / (df['W'] + df['L'])
df['Win_Percentage'] = df['Win_Percentage'].fillna(0.0)

df['Winning_Season'] = (df['Win_Percentage'] > 0.500).astype(int)

X = df[['PF', 'PA', 'PD', 'SoS']]
y = df['Winning_Season']

db_path = os.path.join(script_dir, "NFL.db")
conn = sqlite3.connect(db_path)
df['Confidence'] = None
df.to_sql("stats", conn, if_exists="replace", index=False)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

model = LogisticRegression()
model.fit(X_train, y_train)

with open(os.path.join(script_dir, "model.pkl"), "wb") as f:
    pickle.dump(model, f)
with open(os.path.join(script_dir, "scaler.pkl"), "wb") as f:
    pickle.dump(scaler, f)

vipers_stats = pd.DataFrame([{
    'PF': 465.0,
    'PA': 380.0,
    'PD': 85.0,
    'SoS': 1.5
}])

vipers_scaled = scaler.transform(vipers_stats)
vipers_pred_single = model.predict(vipers_scaled)[0]
vipers_pred = vipers_pred_single.astype(int)
vipers_prob_single = model.predict_proba(vipers_scaled)[0]
vipers_prob = vipers_prob_single.astype(float)

vipers_row = {
    'Tm': 'Atlanta Vipers',
    'W': 0, 'L': 0,
    'PF': 465.0, 'PA': 380.0, 'PD': 85.0, 'SoS': 1.5,
    'Win_Percentage': 0.0,
    'Winning_Season': vipers_pred,
    'Confidence': vipers_prob
}
pd.DataFrame([vipers_row]).to_sql("stats", conn, if_exists="append", index=False)
conn.close()

print(f"\n--- SUCCESS ---")
print(f"Atlanta Vipers predicted outcome: {'Winning Season (1)' if vipers_pred == 1 else 'Losing Season (0)'}")
print(f"Probability of Winning Season: {vipers_prob}")