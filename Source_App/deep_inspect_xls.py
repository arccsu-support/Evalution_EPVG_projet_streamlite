import pandas as pd, json, os, sys

path = r"e:/DIRCOP/Mission evaluation des EPVG en province avec iGS et UG PDSS/Evalution EPVG mission UG PDSS/Formulaire_Habilitation EPVG (1).xlsx"
xls = pd.ExcelFile(path)

out_dir = r"e:/DIRCOP/Mission evaluation des EPVG en province avec iGS et UG PDSS/Evalution EPVG mission UG PDSS"

# 1. Survey: export ALL rows
df_survey = pd.read_excel(xls, sheet_name="survey")
df_survey.to_csv(os.path.join(out_dir, "xls_survey_full.csv"), index=False, encoding="utf-8-sig")
print(f"Survey: {len(df_survey)} rows, columns: {list(df_survey.columns)}")

# 2. Choices: export ALL rows
df_choices = pd.read_excel(xls, sheet_name="choices")
df_choices.to_csv(os.path.join(out_dir, "xls_choices_full.csv"), index=False, encoding="utf-8-sig")
print(f"Choices: {len(df_choices)} rows, columns: {list(df_choices.columns)}")

# 3. Show all unique list_names in choices
print(f"\nUnique list_names: {df_choices['list_name'].unique().tolist()}")

# 4. Show all unique types in survey
print(f"\nUnique types in survey: {df_survey['type'].unique().tolist()}")

# 5. Show 'importance' column values (the severity concept)
if 'importance' in df_survey.columns:
    importance_vals = df_survey['importance'].dropna().unique().tolist()
    print(f"\nUnique 'importance' values: {importance_vals}")
    # Show rows where importance is set
    imp_rows = df_survey[df_survey['importance'].notna()][['type','name','label','importance']]
    imp_rows.to_csv(os.path.join(out_dir, "xls_importance_rows.csv"), index=False, encoding="utf-8-sig")
    print(f"Rows with importance set: {len(imp_rows)}")

# 6. Look for fields with 'begin_group' / 'end_group' to understand structure
groups = df_survey[df_survey['type'].str.contains('group|repeat', case=False, na=False)][['type','name','label']]
groups.to_csv(os.path.join(out_dir, "xls_groups.csv"), index=False, encoding="utf-8-sig")
print(f"\nGroups/repeats: {len(groups)}")

# 7. Look for calculate fields (scores)
calcs = df_survey[df_survey['type'].str.contains('calculate', case=False, na=False)][['type','name','label','calculation']]
calcs.to_csv(os.path.join(out_dir, "xls_calculations.csv"), index=False, encoding="utf-8-sig")
print(f"\nCalculation fields: {len(calcs)}")

# 8. Settings sheet
if 'settings' in xls.sheet_names:
    df_settings = pd.read_excel(xls, sheet_name="settings")
    df_settings.to_csv(os.path.join(out_dir, "xls_settings.csv"), index=False, encoding="utf-8-sig")
    print(f"\nSettings: {df_settings.to_dict(orient='records')}")

# 9. Entities sheet
if 'entities' in xls.sheet_names:
    df_entities = pd.read_excel(xls, sheet_name="entities")
    df_entities.to_csv(os.path.join(out_dir, "xls_entities.csv"), index=False, encoding="utf-8-sig")
    print(f"\nEntities: {len(df_entities)} rows")

print("\nDone. CSV files exported.")
