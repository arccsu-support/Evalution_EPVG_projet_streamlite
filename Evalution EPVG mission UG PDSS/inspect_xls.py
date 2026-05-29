import pandas as pd, json, sys, os
path = r"e:/DIRCOP/Mission evaluation des EPVG en province avec iGS et UG PDSS/Evalution EPVG mission UG PDSS/Formulaire_Habilitation EPVG (1).xlsx"
if not os.path.exists(path):
    print(json.dumps({"error": f"File not found: {path}"}))
    sys.exit(1)
xls = pd.ExcelFile(path)
info = {"sheets": xls.sheet_names}
for sheet in ["survey", "choices"]:
    if sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        # Convert first few rows to list of dicts for brevity
        info[sheet] = {
            "columns": list(df.columns),
            "sample_rows": df.head(5).to_dict(orient="records")
        }
print(json.dumps(info, ensure_ascii=False, indent=2))
