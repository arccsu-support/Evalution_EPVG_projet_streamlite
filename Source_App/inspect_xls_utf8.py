import pandas as pd, json, os, sys
path = r"e:/DIRCOP/Mission evaluation des EPVG en province avec iGS et UG PDSS/Evalution EPVG mission UG PDSS/Formulaire_Habilitation EPVG (1).xlsx"
if not os.path.exists(path):
    sys.exit("File not found")
xls = pd.ExcelFile(path)
info = {"sheets": xls.sheet_names}
for sheet in ["survey", "choices"]:
    if sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        info[sheet] = {
            "columns": list(df.columns),
            "sample_rows": df.head(5).to_dict(orient="records")
        }
out_path = r"e:/DIRCOP/Mission evaluation des EPVG en province avec iGS et UG PDSS/Evalution EPVG mission UG PDSS/xls_info.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=2)
print(f"Info written to {out_path}")
