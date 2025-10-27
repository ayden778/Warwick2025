# Task B — Stack Overflow Developer Survey 2025 Analytics#
import pandas as pd
import re
from typing import Optional

df_raw = pd.DataFrame(reader.get_data())
print(f"Loaded {len(df_raw):,} survey responses\n")

print("A quick peek at columns (may vary slightly year-to-year):")
print(df_raw.columns.tolist(), "\n")

def parse_years(value: Optional[str]) -> Optional[float]:
    if pd.isna(value):
        return None
    s = str(value).strip()
    if s.lower().startswith("less than"):
        return 0.5
    if s.lower().startswith("more than"):
        m = re.search(r"\d+", s)
        return float(m.group()) if m else 50.0
    try:
        return float(s)
    except ValueError:
        return None

if "YearsCode" in df_raw.columns:
    df_raw["YearsCodeNum"] = df_raw["YearsCode"].map(parse_years)
if "YearsCodePro" in df_raw.columns:
    df_raw["YearsCodeProNum"] = df_raw["YearsCodePro"].map(parse_years)
    df_raw["NonProfessionalYears"] = df_raw["YearsCodeNum"] - df_raw["YearsCodeProNum"]

# Q1: Print all of the questions asked in the survey
print("Q1: All questions in the survey (from schema)")
schema = pd.DataFrame(reader.get_schema())

text_cols = [c for c in schema.columns if "question" in c.lower() or "text" in c.lower()]
if text_cols:
    qcol = text_cols[0]
    for i, row in schema[[qcol]].dropna().iterrows():
        print("-", row[qcol])
else:
    print("(Could not find a single question-text column; here is a schema preview)")
    display(schema.head())

print("\n")  # spacing

# Q2: Which age range has the most responses?
print("Q2: Most common age bracket")
if "Age" in df_raw.columns:
    counts = df_raw["Age"].value_counts(dropna=True)
    top_age = counts.idxmax()
    print(f"Most common age range: {top_age} ({counts.max():,} responses)")
else:
    print("Age column not present in this dataset.")
print()

# Q3: How many people work at companies larger than Marshall Wace?
def orgsize_lower_bound(s: Optional[str]) -> Optional[int]:
    if pd.isna(s):
        return None
    nums = re.findall(r"\d[\d,]*", str(s))
    if not nums:
        return None
    return int(nums[0].replace(",", ""))

print("Q3: Respondents at companies larger than Marshall Wace (~1500 employees)")
if "OrgSize" in df_raw.columns:
    df_raw["OrgSizeLower"] = df_raw["OrgSize"].map(orgsize_lower_bound)
    count_larger = int((df_raw["OrgSizeLower"].fillna(-1) > 1500).sum())
    print(f"Number of respondents working at companies with >1500 employees: {count_larger}")
    thresholds = [500, 1000, 1500, 2000, 5000]
    summary = {t: int((df_raw["OrgSizeLower"].fillna(-1) > t).sum()) for t in thresholds}
    print("Quick thresholds (employees -> count):", summary)
else:
    print("OrgSize column not present in this dataset.")
print()

# Q4: How many respondents had < 1 year of coding experience outside their job?
print("Q4: Respondents with <1 year of non-professional coding experience")
if "NonProfessionalYears" in df_raw.columns:
    mask = df_raw["NonProfessionalYears"].notna() & (df_raw["NonProfessionalYears"] < 1.0)
    print("Count:", int(mask.sum()))
else:
    print("NonProfessionalYears not available (YearsCode / YearsCodePro missing).")
print()

# Q5: For people with 1+ non-pro years, what's the average non-professional years?
print("Q5: Average non-professional years for exact numeric entries (1–50 years)")
if {"YearsCodeNum", "YearsCodeProNum", "NonProfessionalYears"}.issubset(df_raw.columns):
    def is_plain_number_str(x):
        if pd.isna(x):
            return False
        s = str(x).strip()
        return s.isdigit()
    mask_exact = df_raw["YearsCode"].map(is_plain_number_str) & df_raw["YearsCodePro"].map(is_plain_number_str)
    subset = df_raw[mask_exact].copy()
    subset["NonProfessionalYears"] = subset["YearsCodeNum"] - subset["YearsCodeProNum"]
    subset_valid = subset[subset["NonProfessionalYears"].between(1, 50)]
    avg_nonpro = subset_valid["NonProfessionalYears"].mean()
    if pd.isna(avg_nonpro):
        print("Not enough exact numeric entries to compute a reliable average.")
    else:
        print("Average non-professional coding years (1–50, exact entries):", round(avg_nonpro, 2))
else:
    print("Required year columns missing; cannot compute this metric.")
print()

# Q6: Median annual total compensation in USD
print("Q6: Median annual total compensation (USD)")
comp_col = "ConvertedCompYearly" if "ConvertedCompYearly" in df_raw.columns else None
if comp_col:
    comp_series = pd.to_numeric(df_raw[comp_col], errors="coerce")
    med = comp_series.dropna().median()
    if pd.isna(med):
        print("No valid compensation numbers found.")
    else:
        print("Median (USD):", int(round(med, 0)))
else:
    print("Compensation column not found.")
print()

# Q7: Which programming language has respondents with the highest annual compensation?
print("Q7: Language with highest median annual compensation (USD)")

if {"LanguageHaveWorkedWith", "ConvertedCompYearly"}.issubset(df_raw.columns):
    df_lang = df_raw[["LanguageHaveWorkedWith", "ConvertedCompYearly"]].dropna()
    df_lang["ConvertedCompYearly"] = pd.to_numeric(df_lang["ConvertedCompYearly"], errors="coerce")
    df_lang = df_lang.dropna(subset=["ConvertedCompYearly"])
    df_lang["LanguageHaveWorkedWith"] = df_lang["LanguageHaveWorkedWith"].str.split(";")
    df_lang = df_lang.explode("LanguageHaveWorkedWith")
    df_lang["LanguageHaveWorkedWith"] = df_lang["LanguageHaveWorkedWith"].str.strip()
    df_lang = df_lang[df_lang["LanguageHaveWorkedWith"] != ""]
    lang_stats = df_lang.groupby("LanguageHaveWorkedWith")["ConvertedCompYearly"].agg(["median", "count"]).sort_values("median", ascending=False)
    print("Top 10 languages by median compensation (USD):")
    display(lang_stats.head(10))
    top = lang_stats.index[0] if not lang_stats.empty else None
    print("Language with highest median pay:", top)
else:
    print("Language or compensation column missing; cannot compute.")
print()

# Bonus: small performance improvement for SurveyDataReader
print("Bonus: creating a FastSurveyDataReader (tiny optimisation)")

class FastSurveyDataReader(SurveyDataReader):
    def __init__(self, schema_file: str, data_file: str):
        super().__init__(schema_file, data_file)
        self._by_id = {row["ResponseId"]: row for row in self.data}

    def get_response_by_id(self, response_id):
        return self._by_id.get(str(response_id))

fast_reader = FastSurveyDataReader(SCHEMA_RELATIVE_PATH, DATA_RELATIVE_PATH)
sample_id = reader.get_data()[0]["ResponseId"]
assert fast_reader.get_response_by_id(sample_id) == reader.get_response_by_id(sample_id)
print("FastSurveyDataReader ready — lookups are O(1).\n")

print("All done. Save this as TaskB.ipynb and include it with TaskA.ipynb, environment.yml and the data folder.")
