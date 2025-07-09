# from flask import Flask, render_template, request, jsonify
# from flask_cors import CORS
# import pandas as pd
# import gspread
# import re
# from oauth2client.service_account import ServiceAccountCredentials
# from urllib.parse import unquote
# from datetime import datetime
# from dateutil import parser

# app = Flask(__name__)
# CORS(app)

# # --- Google Sheets Setup ---
# scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
# client = gspread.authorize(creds)

# # --- Sheet URLs and Worksheet Names ---
# sheet1_url = "https://docs.google.com/spreadsheets/d/1vDs8Y2eYMzxGF4-6Q0kT0zbEFxPc6ltUSCOli0zEU1w/edit" # Jang
# sheet2_url = "https://docs.google.com/spreadsheets/d/1VBYefutul8-Hfh1iOUmSsLe6EHDkO_4Ajm_Dfsk9RW4/edit" # Lifestyle 
# sheet1 = client.open_by_url(sheet1_url).sheet1
# sheet2 = client.open_by_url(sheet2_url).worksheet("Date Wise Trends")

# # --- Normalize Date ---
# def normalize_date_string(date_str):
#     try:
#         date_str = date_str.strip().replace("(", "").replace(")", "").replace(" / ", "/").replace(" /", "/").replace("/ ", "/")
#         if ':' in date_str:
#             date_str = date_str.split()[0]
#         parsed_date = parser.parse(date_str, dayfirst=True)
#         return parsed_date.strftime("%Y-%m-%d")
#     except Exception:
#         return date_str

# # --- Strategy Cloud ---
# def load_strategy_data():
#     data = sheet1.get_all_records()
#     df = pd.DataFrame(data)
#     df.rename(columns={"secondary keyword or primary": "sec_pri", "DATE": "Date"}, inplace=True)  # Use column K
#     df["Date"] = pd.to_datetime(df["Date"].apply(normalize_date_string), errors='coerce').dt.date
#     df.fillna("", inplace=True)
#     return df

# @app.route("/keywords/<date>")
# def get_primary_secondary(date):
#     try:
#         df = load_strategy_data()
#         target_date = pd.to_datetime(normalize_date_string(date)).date()
#         filtered = df[df["Date"] == target_date]
#         primary = filtered[filtered["sec_pri"].str.lower() == "primary"]["Keyword"].str.strip().str.lower().dropna().unique().tolist()
#         secondary = filtered[filtered["sec_pri"].str.lower() == "secondary"]["Keyword"].str.strip().str.lower().dropna().unique().tolist()
#         return jsonify({"primary": primary, "secondary": secondary})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/strategy_data/<date>/<keyword>/<type>")
# def get_strategy_data(date, keyword, type):
#     try:
#         df = load_strategy_data()
#         target_date = pd.to_datetime(normalize_date_string(date)).date()
#         keyword = unquote(keyword).strip().lower()
#         type = type.lower()
#         filtered = df[
#             (df["Date"] == target_date) &
#             (df["Keyword"].str.strip().str.lower() == keyword) &
#             (df["sec_pri"].str.lower() == type)
#         ]
#         return jsonify(filtered.to_dict(orient="records"))
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# # --- Matching Keywords Cloud ---
# @app.route("/matching_keywords", methods=["POST"])
# def keyword_matching():
#     try:
#         data = request.get_json()
#         selected_date = normalize_date_string(data['date'])

#         keywords = sheet2.col_values(1)[1:]
#         volumes = sheet2.col_values(4)[1:]
#         dates = [normalize_date_string(d) for d in sheet2.col_values(12)[1:]]  # Use column L

#         full_data = {}
#         for kw, vol, dt in zip(keywords, volumes, dates):
#             if dt == selected_date:
#                 try:
#                     v = int(vol.replace(',', ''))
#                     if kw:
#                         full_data[kw.strip()] = v
#                 except ValueError:
#                     continue

#         sorted_keywords = sorted(full_data.items(), key=lambda x: x[1], reverse=True)[:20]
#         max_volume = max([v for k, v in sorted_keywords], default=1)

#         top_keywords = [
#             {'word': k, 'size': int((v / max_volume) * 30 + 12), 'volume': v}
#             for k, v in sorted_keywords
#         ]

#         return jsonify(top_keywords=top_keywords)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# # --- Frequency Match Cloud (Third Cloud) ---
# @app.route("/get_data", methods=["POST"])
# def get_data():
#     try:
#         data = request.get_json()
#         selected_date = normalize_date_string(data['date'])
#         selected_date = pd.to_datetime(selected_date).date()

#         # --- Sheet1 ---
#         sheet1_data = sheet1.get_all_records()
#         df1 = pd.DataFrame(sheet1_data)
#         df1.rename(columns={"DATE": "Date"}, inplace=True)
#         df1["Date"] = pd.to_datetime(df1["Date"].apply(normalize_date_string), errors='coerce').dt.date
#         df1.fillna("", inplace=True)

#         # --- Sheet2 ---
#         sheet2_data = sheet2.get_all_records()
#         df2 = pd.DataFrame(sheet2_data)
#         df2.rename(columns={"DATE 2": "Date"}, inplace=True)
#         df2["Date"] = pd.to_datetime(df2["Date"].apply(normalize_date_string), errors='coerce').dt.date
#         df2.fillna("", inplace=True)

#         # --- Filter by Date ---
#         df1_filtered = df1[df1["Date"] == selected_date]
#         df2_filtered = df2[df2["Date"] == selected_date]

#         # --- Combine All Keywords ---
#         keywords1 = df1_filtered["Keyword"].dropna().astype(str).str.lower()
#         keywords2 = pd.concat([
#             df2_filtered["Trending Keywords/Topic"].dropna().astype(str).str.lower(),
#             df2_filtered["Keywords"].dropna().astype(str).str.lower()
#         ])
#         all_keywords = pd.concat([keywords1, keywords2]).unique()

#         results = []
#         for kw in all_keywords:
#             sheet1_matches = df1_filtered[df1_filtered["Keyword"].astype(str).str.lower().str.contains(kw, na=False)]
#             sheet2_matches = df2_filtered[
#                 df2_filtered["Trending Keywords/Topic"].astype(str).str.lower().str.contains(kw, na=False) |
#                 df2_filtered["Keywords"].astype(str).str.lower().str.contains(kw, na=False)
#             ]

#             if not sheet1_matches.empty or not sheet2_matches.empty:
#                 results.append({
#                     "keyword": kw,
#                     "count": len(sheet1_matches) + len(sheet2_matches),
#                     "sheet1_rows": sheet1_matches.to_dict(orient="records"),
#                     "sheet2_rows": sheet2_matches.to_dict(orient="records")
#                 })

#         return jsonify({"results": results})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# # --- Data Table API 
# @app.route("/get_table_data", methods=["POST"])
# def get_table_data():
#     try:
#         data = request.get_json()
#         keyword = data['keyword']
#         selected_date = normalize_date_string(data['date'])

#         headers = sheet2.row_values(1)
#         keyword_col = sheet2.col_values(1)[1:]
#         dates_col = [normalize_date_string(d) for d in sheet2.col_values(12)[1:]]  # Use column L

#         rows = []
#         for i, (kw, date) in enumerate(zip(keyword_col, dates_col)):
#             if selected_date == date and re.search(r'\b' + re.escape(keyword.lower()) + r'\b', kw.lower()):
#                 row = sheet2.row_values(i + 2)
#                 row += [""] * (len(headers) - len(row))
#                 row_dict = dict(zip(headers, row))
#                 row_dict["keyword"] = kw  # Ensure keyword field exists for frontend
#                 rows.append(row_dict)

#         return jsonify(rows=rows)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400




# @app.route("/")
# def home():
#     return render_template("home1.html")

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

def register_keyword_routes(app):
    from flask import render_template, request, jsonify

    import pandas as pd
    import gspread
    import re
    from oauth2client.service_account import ServiceAccountCredentials
    from urllib.parse import unquote
    from datetime import datetime
    from dateutil import parser


    # --- Google Sheets Setup ---
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    # --- Sheet URLs and Worksheet Names ---
    sheet1_url = "https://docs.google.com/spreadsheets/d/1vDs8Y2eYMzxGF4-6Q0kT0zbEFxPc6ltUSCOli0zEU1w/edit"
    sheet2_url = "https://docs.google.com/spreadsheets/d/1VBYefutul8-Hfh1iOUmSsLe6EHDkO_4Ajm_Dfsk9RW4/edit"
    sheet1 = client.open_by_url(sheet1_url).sheet1
    sheet2 = client.open_by_url(sheet2_url).worksheet("Date Wise Trends")

    def normalize_date_string(date_str):
        try:
            date_str = date_str.strip().replace("(", "").replace(")", "").replace(" / ", "/").replace(" /", "/").replace("/ ", "/")
            if ':' in date_str:
                date_str = date_str.split()[0]
            parsed_date = parser.parse(date_str, dayfirst=True)
            return parsed_date.strftime("%Y-%m-%d")
        except Exception:
            return date_str

    def load_strategy_data():
        data = sheet1.get_all_records()
        df = pd.DataFrame(data)
        df.rename(columns={"secondary keyword or primary": "sec_pri", "DATE": "Date"}, inplace=True)
        df["Date"] = pd.to_datetime(df["Date"].apply(normalize_date_string), errors='coerce').dt.date
        df.fillna("", inplace=True)
        return df

    @app.route("/keywords/<date>")
    def get_primary_secondary(date):
        try:
            df = load_strategy_data()
            target_date = pd.to_datetime(normalize_date_string(date)).date()
            filtered = df[df["Date"] == target_date]
            primary = filtered[filtered["sec_pri"].str.lower() == "primary"]["Keyword"].str.strip().str.lower().dropna().unique().tolist()
            secondary = filtered[filtered["sec_pri"].str.lower() == "secondary"]["Keyword"].str.strip().str.lower().dropna().unique().tolist()
            return jsonify({"primary": primary, "secondary": secondary})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/strategy_data/<date>/<keyword>/<type>")
    def get_strategy_data(date, keyword, type):
        try:
            df = load_strategy_data()
            target_date = pd.to_datetime(normalize_date_string(date)).date()
            keyword = unquote(keyword).strip().lower()
            type = type.lower()
            filtered = df[
                (df["Date"] == target_date) &
                (df["Keyword"].str.strip().str.lower() == keyword) &
                (df["sec_pri"].str.lower() == type)
            ]
            return jsonify(filtered.to_dict(orient="records"))
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/matching_keywords", methods=["POST"])
    def keyword_matching():
        try:
            data = request.get_json()
            selected_date = normalize_date_string(data['date'])
            keywords = sheet2.col_values(1)[1:]
            volumes = sheet2.col_values(4)[1:]
            dates = [normalize_date_string(d) for d in sheet2.col_values(12)[1:]]
            full_data = {}
            for kw, vol, dt in zip(keywords, volumes, dates):
                if dt == selected_date:
                    try:
                        v = int(vol.replace(',', ''))
                        if kw:
                            full_data[kw.strip()] = v
                    except ValueError:
                        continue
            sorted_keywords = sorted(full_data.items(), key=lambda x: x[1], reverse=True)[:20]
            max_volume = max([v for k, v in sorted_keywords], default=1)
            top_keywords = [
                {'word': k, 'size': int((v / max_volume) * 30 + 12), 'volume': v}
                for k, v in sorted_keywords
            ]
            return jsonify(top_keywords=top_keywords)
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    

        

    @app.route("/get_data", methods=["POST"])
    def get_data():
        try:
            data = request.get_json()
            selected_date = normalize_date_string(data['date'])
            selected_date = pd.to_datetime(selected_date).date()
            sheet1_data = sheet1.get_all_records()
            df1 = pd.DataFrame(sheet1_data)
            df1.rename(columns={"DATE": "Date"}, inplace=True)
            df1["Date"] = pd.to_datetime(df1["Date"].apply(normalize_date_string), errors='coerce').dt.date
            df1.fillna("", inplace=True)
            sheet2_data = sheet2.get_all_records()
            df2 = pd.DataFrame(sheet2_data)
            df2.rename(columns={"DATE 2": "Date"}, inplace=True)
            df2["Date"] = pd.to_datetime(df2["Date"].apply(normalize_date_string), errors='coerce').dt.date
            df2.fillna("", inplace=True)
            df1_filtered = df1[df1["Date"] == selected_date]
            df2_filtered = df2[df2["Date"] == selected_date]
            keywords1 = df1_filtered["Keyword"].dropna().astype(str).str.lower()
            keywords2 = pd.concat([
                df2_filtered["Trending Keywords/Topic"].dropna().astype(str).str.lower(),
                df2_filtered["Keywords"].dropna().astype(str).str.lower()
            ])
            all_keywords = pd.concat([keywords1, keywords2]).unique()
            results = []
            for kw in all_keywords:
                sheet1_matches = df1_filtered[df1_filtered["Keyword"].astype(str).str.lower().str.contains(kw, na=False)]
                sheet2_matches = df2_filtered[
                    df2_filtered["Trending Keywords/Topic"].astype(str).str.lower().str.contains(kw, na=False) |
                    df2_filtered["Keywords"].astype(str).str.lower().str.contains(kw, na=False)
                ]
                if not sheet1_matches.empty or not sheet2_matches.empty:
                    results.append({
                        "keyword": kw,
                        "count": len(sheet1_matches) + len(sheet2_matches),
                        "sheet1_rows": sheet1_matches.to_dict(orient="records"),
                        "sheet2_rows": sheet2_matches.to_dict(orient="records")
                    })
            return jsonify({"results": results})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/get_table_data", methods=["POST"])
    def get_table_data():
        try:
            data = request.get_json()
            keyword = data['keyword']
            selected_date = normalize_date_string(data['date'])

            headers = sheet2.row_values(1)
            keyword_col = sheet2.col_values(1)[1:]  # Column A: "Keywords"
            dates_col = [normalize_date_string(d) for d in sheet2.col_values(12)[1:]]  # Column L: "DATE 2"

            rows = []
            for i, (kw, date) in enumerate(zip(keyword_col, dates_col)):
                if not kw or not date:
                    continue

                kw_clean = kw.strip().lower()
                keyword_clean = keyword.strip().lower()

                if selected_date == date and keyword_clean in kw_clean:
                    row = sheet2.row_values(i + 2)
                    row += [""] * (len(headers) - len(row))  # pad missing columns
                    row_dict = dict(zip(headers, row))
                    row_dict["keyword"] = kw_clean  # for frontend usage
                    rows.append(row_dict)

            return jsonify(rows=rows)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/keyword-home")
    def keyword_home():
        return render_template("home1.html")

