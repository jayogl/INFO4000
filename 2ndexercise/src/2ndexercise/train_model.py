import pandas as pd
import numpy as np
import sqlite3
import pickle
import re
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

# =====================================================================
# TASK 1: Scrape Data from ESPN [7]
# =====================================================================
url = "https://www.espn.com/nfl/standings"
tables = pd.read_html(url)

# ESPN's Table Layout:
# Table 0: AFC Team Names | Table 1: AFC Stats (W, L, PF, PA, etc.)
# Table 2: NFC Team Names | Table 3: NFC Stats (W, L, PF, PA, etc.)
afc_names = tables
afc_stats = tables[9]
nfc_names = tables[1]
nfc_stats = tables[7]

# =====================================================================
# TASK 2: Combine & Clean Conference Data [7]
# =====================================================================
# ESPN renders the header row as row 0 in the data. Reassign it as columns.
afc_stats.columns = afc_stats.iloc
afc_stats = afc_stats[1:].reset_index(drop=True)

nfc_stats.columns = nfc_stats.iloc
nfc_stats = nfc_stats[1:].reset_index(drop=True)

# Merge names and stats horizontally
afc = pd.concat([afc_names, afc_stats], axis=1)
nfc = pd.concat([nfc_names, nfc_stats], axis=1)

# Concatenate AFC and NFC vertically to compile all 32 teams
df = pd.concat([afc, nfc], ignore_index=True)

# =====================================================================
# TASK 3: Feature Engineering & Cleaning [8]
# =====================================================================
# Rename the first column (holding names) to 'Tm'
df.rename(columns={df.columns: 'Tm'}, inplace=True)

# Clean team names (remove playoff indicators like "x - ", "y - " or seeding numbers)
def clean_team_name(name):
    if not isinstance(name, str):
        return name
    name = re.sub(r'^[a-z]\s*-\s*', '', name)  # removes clinching prefixes
    name = re.sub(r'^\d+\s*', '', name)       # removes starting seeds
    name = re.sub(r'\s*\d+$', '', name)       # removes ending seeds
    return name.strip()

df['Tm'] = df['Tm'].apply(clean_team_name)

# Convert key statistics to floats
df['PF'] = pd.to_numeric(df['PF'], errors='coerce').astype(float)
df['PA'] = pd.to_numeric(df['PA'], errors='coerce').astype(float)

# Calculate Point Differential: PD = PF - PA
df['PD'] = df['PF'] - df['PA']

# Ensure Strength of Schedule (SoS) exists; populate with 0.0 if not present [8]
if 'SoS' not in df.columns:
    df['SoS'] = 0.0
else:
    df['SoS'] = pd.to_numeric(df['SoS'], errors='coerce').fillna(0.0).astype(float)

# Ensure Win (W) and Loss (L) are numeric
df['W'] = pd.to_numeric(df['W'], errors='coerce').fillna(0).astype(int)
df['L'] = pd.to_numeric(df['L'], errors='coerce').fillna(0).astype(int)

# =====================================================================
# TASKS 4 & 5: Prevent Data Leakage & Create Target Label [2, 8]
# =====================================================================
# Calculate Win Percentage strictly to define target threshold
df['Win_Percentage'] = df['W'] / (df['W'] + df['L'])
df['Win_Percentage'] = df['Win_Percentage'].fillna(0.0)

# Binary target: 1 for a winning season (> 0.500 win rate), 0 otherwise
df['Winning_Season'] = (df['Win_Percentage'] > 0.500).astype(int)

# Drop W, L, and Win_Percentage from feature set to avoid target leakage [2, 8]
X = df[['PF', 'PA', 'PD', 'SoS']]
y = df['Winning_Season']

# =====================================================================
# TASK 6: SQLite Storage [2]
# =====================================================================
conn = sqlite3.connect("NFL.db")
df.to_sql("stats", conn, if_exists="replace", index=False)

# =====================================================================
# TASK 7: Model Training & Scaling [2]
# =====================================================================
# Standardize features (highly recommended for Logistic Regression with varying feature scales)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

model = LogisticRegression()
model.fit(X_train, y_train)

# Save the trained model and scaler to pickles for deployment
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)
with open("scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

# =====================================================================
# TASK 8: Predict on New Data (Atlanta Vipers) [3]
# =====================================================================
vipers_stats = pd.DataFrame([{
    'PF': 465.0,
    'PA': 380.0,
    'PD': 85.0,  # PF - PA (465 - 380)
    'SoS': 1.5
}])

# Transform using the exact same scaler
vipers_scaled = scaler.transform(vipers_stats)
vipers_pred = int(model.predict(vipers_scaled))
vipers_prob = float(model.predict_proba(vipers_scaled)[9])

# Append the hypothetical team's row to the SQLite database
vipers_row = {
    'Tm': 'Atlanta Vipers',
    'W': 0, 'L': 0,
    'PF': 465.0, 'PA': 380.0, 'PD': 85.0, 'SoS': 1.5,
    'Win_Percentage': 0.0,
    'Winning_Season': vipers_pred
}
pd.DataFrame([vipers_row]).to_sql("stats", conn, if_exists="append", index=False)
conn.close()

print("Database populated, model trained successfully, and Vipers record appended!")
print(f"Atlanta Vipers predicted outcome: {'Winning Season' if vipers_pred == 1 else 'Losing Season'}")
print(f"Model Confidence (Probability of Winning Season): {vipers_prob:.2%}")