import pandas as pd, json, os

survey_path = "xls_survey_full.csv"
choices_path = "xls_choices_full.csv"

df_survey = pd.read_csv(survey_path)
df_choices = pd.read_csv(choices_path)

# Let's inspect the questions with 'importance'
importance_rows = df_survey[df_survey['importance'].notna()].copy()

# Standardize importance column: remove trailing spaces and lowercase
importance_rows['importance_clean'] = importance_rows['importance'].astype(str).str.strip().str.lower()

# Map the clean importance to standard categories
# c -> critique, ma -> majeur, mi -> mineur, re -> remarque
map_importance = {
    'c': 'Critique',
    'ma': 'Majeur',
    'mi': 'Mineur',
    're': 'Remarque'
}
importance_rows['severity_level'] = importance_rows['importance_clean'].map(map_importance)

# Check what types of questions have importance
type_counts = importance_rows['type'].value_counts().to_dict()

# Let's see the choices list names used by these questions
# In XLSForm, the type is 'select_one [list_name]'
importance_rows['list_name'] = importance_rows['type'].apply(
    lambda x: x.split(' ')[1] if isinstance(x, str) and x.startswith('select_one ') else None
)

# For each unique list_name, let's see what are the choices options
choices_by_list = {}
unique_lists = importance_rows['list_name'].dropna().unique()
for lst in unique_lists:
    lst_choices = df_choices[df_choices['list_name'] == lst]
    choices_by_list[lst] = lst_choices[['name', 'label']].to_dict(orient='records')

# Let's write an analysis summary
analysis = {
    "total_questions_with_importance": len(importance_rows),
    "importance_distribution": importance_rows['severity_level'].value_counts().to_dict(),
    "importance_raw_distribution": importance_rows['importance'].value_counts().to_dict(),
    "type_counts": type_counts,
    "list_choices": choices_by_list,
    "sample_questions_with_importance": importance_rows[['name', 'label', 'importance', 'type']].head(20).to_dict(orient='records')
}

with open("importance_analysis.json", "w", encoding="utf-8") as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)

print("Analysis written to importance_analysis.json")
# Let's check some calculations too
calculate_rows = df_survey[df_survey['type'] == 'calculate'].copy()
print(f"Total calculate rows: {len(calculate_rows)}")
# Check calculations related to score, severity, or totals
score_calcs = calculate_rows[calculate_rows['name'].str.contains('score|total|pourcentage|conforme|sante', case=False, na=False)]
print(f"Score-related calculate rows: {len(score_calcs)}")
score_calcs[['name', 'calculation', 'label']].head(20).to_csv("score_calculations_sample.csv", index=False, encoding="utf-8-sig")
