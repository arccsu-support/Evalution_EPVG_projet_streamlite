import pandas as pd, json

df_survey = pd.read_csv("xls_survey_full.csv")
image_rows = df_survey[df_survey['type'] == 'image'].copy()
image_fields = image_rows[['name', 'label']].to_dict(orient='records')

with open("image_fields.json", "w", encoding="utf-8") as f:
    json.dump(image_fields, f, ensure_ascii=False, indent=2)

print(f"Found {len(image_fields)} image fields, written to image_fields.json")
