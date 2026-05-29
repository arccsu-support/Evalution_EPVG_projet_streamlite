import pandas as pd, json

df_survey = pd.read_csv("xls_survey_full.csv")
calcs = df_survey[df_survey['type'] == 'calculate'].copy()
calcs_list = calcs[['name', 'calculation', 'label']].dropna(subset=['calculation']).to_dict(orient='records')

with open("calculations_list.json", "w", encoding="utf-8") as f:
    json.dump(calcs_list, f, ensure_ascii=False, indent=2)

print(f"Written {len(calcs_list)} calculations to calculations_list.json")
