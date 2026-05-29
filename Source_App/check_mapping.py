import pandas as pd, json

# Load files
survey_df = pd.read_csv("xls_survey_full.csv")
choices_df = pd.read_csv("xls_choices_full.csv")

# 1. Let's find columns in the survey sheet that match our interest:
# - establishment name
# - location (province, town, zone)
# - GPS
# - date
# - score / percentages / totals

establishment_cols = survey_df[survey_df['name'].str.contains('etab|pharma|nom', case=False, na=False)][['type', 'name', 'label']].to_dict(orient='records')
location_cols = survey_df[survey_df['name'].str.contains('prov|ville|zone|sante', case=False, na=False)][['type', 'name', 'label']].to_dict(orient='records')
gps_cols = survey_df[survey_df['type'].str.contains('geopoint', case=False, na=False)][['type', 'name', 'label']].to_dict(orient='records')
date_cols = survey_df[survey_df['type'].str.contains('date', case=False, na=False)][['type', 'name', 'label']].to_dict(orient='records')
percentage_cols = survey_df[survey_df['name'].str.contains('pourcentage', case=False, na=False)][['type', 'name', 'calculation']].to_dict(orient='records')
total_cols = survey_df[survey_df['name'].str.contains('total', case=False, na=False)][['type', 'name', 'calculation']].to_dict(orient='records')

mapping_summary = {
    "establishment_cols": establishment_cols,
    "location_cols": location_cols,
    "gps_cols": gps_cols,
    "date_cols": date_cols,
    "percentage_cols": percentage_cols,
    "total_cols": total_cols
}

with open("mapping_summary.json", "w", encoding="utf-8") as f:
    json.dump(mapping_summary, f, ensure_ascii=False, indent=2)

print("Mapping summary written to mapping_summary.json")

# Let's also check if all RUBRIQUE_LABELS percentages exist as calculate columns in XLSForm
# In scoring.py: SCORE_COLUMNS = ["a_pourcentage", "b_pourcentage", "c_pourcentage", "d_pourcentage", "e_pourcentage", "f_pourcentage", "g_pourcentage", "h_pourcentage", "i_pourcentage"]
# Let's check their presence and calculations
for col in ["a_pourcentage", "b_pourcentage", "c_pourcentage", "d_pourcentage", "e_pourcentage", "f_pourcentage", "g_pourcentage", "h_pourcentage", "i_pourcentage"]:
    found = survey_df[survey_df['name'] == col]
    if not found.empty:
        print(f"✅ {col} found, calculation: {found.iloc[0]['calculation']}")
    else:
        print(f"❌ {col} NOT found in XLSForm survey!")

# Let's check if 'total' exists
found_total = survey_df[survey_df['name'] == 'total']
if not found_total.empty:
    print(f"✅ 'total' found, calculation: {found_total.iloc[0]['calculation']}")
else:
    print(f"❌ 'total' NOT found in XLSForm survey!")
