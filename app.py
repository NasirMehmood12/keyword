
from flask import Flask, render_template, send_file, request, redirect, url_for
from googleapiclient.discovery import build
import psycopg2
import io
import pandas as pd
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
from datetime import datetime
from flask_cors import CORS
from app4cop import register_keyword_routes 

# Initialize Flask app
app = Flask(__name__)
CORS(app)
register_keyword_routes(app)  # ✅ This should run immediately when the app starts

# YouTube API
API_KEY = 'AIzaSyBMl7RI4kQyeedDS12kjM-YekY3TtKydH4'
youtube_key = build('youtube', 'v3', developerKey=API_KEY)

# News channels dictionary
channels_to_check = {
    "Geo News":        "UC_vt34wimdCzdkrzVejwX9g",
    "ARY News":        "UCMmpLL2ucRHAXbNHiCPyIyg",
    "SAMAA TV":        "UCJekW1Vj5fCVEGdye_mBN6Q",
    "Dunya News":      "UCnMBV5Iw4WqKILKue1nP6Hg",
    "92 News HD":      "UCsgC5cbz3DE2Shh34gNKiog",
    "BOL News":        "UCz2yxQJZgiB_5elTzqV7FiQ",
    "Express News":    "UCTur7oM6mLL0rM2k0znuZpQ",
    "HUM News":        "UC0Um3pnZ2WGBEeoA3BX2sKw",
    "GNN":             "UC35KuZBNIj4S5Ls0yjY-UHQ",
    "Public News":     "UCElJZvY_RVra6qjD8WSQYog",
    "Aaj News":        "UCgBAPAcLsh_MAPvJprIz89w",
    "24 News HD":      "UCcmpeVbSSQlZRvHfdC-CRwg",
    "Neo News HD":     "UCAsvFcpUQegneSh0QAUd64A",
    "City 42":         "UCdTup4kK7Ze08KYp7ReiuMw",
    "Abb Takk News":   "UC5mwDEzm4FzXKoHPBDnuUQQ"
}

channel_ids = set(channels_to_check.values())
id_to_name   = {cid:name for name, cid in channels_to_check.items()}

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        "postgresql://neondb_owner:npg_LWYK2wRoc7QJ@ep-red-violet-a45y3nzx-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
    )

# ---------------- Database Routes ----------------

USERNAME = "IMM"
PASSWORD = "imm@geotv"

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        if user == USERNAME and pw == PASSWORD:
            return redirect(url_for('youtube'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/youtube')
def youtube():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, subscribers, views, videos FROM youtube_stats order by subscribers desc")
        stats_data = cursor.fetchall()
        cursor.close()
        conn.close()

        if not stats_data:
            return render_template('youtube.html', error="No data found")
        return render_template('youtube.html', stats_data=stats_data)
    except Exception as e:
        return f"Database error: {e}"

@app.route('/facebook')
def facebook():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT page_name, follower, likes, following
FROM facebook_stats
ORDER BY
  CASE
    WHEN LOWER(follower) LIKE '%m%' THEN 
      REPLACE(LOWER(follower), 'm followers', '')::FLOAT * 1000000
    WHEN LOWER(follower) LIKE '%k%' THEN 
      REPLACE(LOWER(follower), 'k followers', '')::FLOAT * 1000
    ELSE
      REPLACE(LOWER(follower), 'followers', '')::FLOAT
  END DESC;""")
        stats_data = cursor.fetchall()
        cursor.close()
        conn.close()

        if not stats_data:
            return render_template('facebook.html', error="No data found")
        return render_template('facebook.html', stats_data=stats_data)
    except Exception as e:
        return f"Database error: {e}"
    

@app.route("/keyword_tool")
def keyword_tool():
    return redirect("/keyword-home")    

@app.route('/instagram')
def instagram():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """ SELECT page_name, followers, following, posts
    FROM instagram_stats
    ORDER BY
      CASE
        WHEN LOWER(followers) LIKE '%m%' THEN 
          REGEXP_REPLACE(LOWER(followers), '[^0-9.]', '', 'g')::FLOAT * 1000000
        WHEN LOWER(followers) LIKE '%k%' THEN 
          REGEXP_REPLACE(LOWER(followers), '[^0-9.]', '', 'g')::FLOAT * 1000
        ELSE
          REGEXP_REPLACE(LOWER(followers), '[^0-9.]', '', 'g')::FLOAT
      END DESC;""")
        stats_data = cursor.fetchall()
        cursor.close()
        conn.close()

        if not stats_data:
            return render_template('instagram.html', error="No data found")
        return render_template('instagram.html', stats_data=stats_data)
    except Exception as e:
        return f"Database error: {e}"

@app.route('/simple_stats')
def all_channel_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        channels = {
            "GEO News": "youtube_videos",
            "ARY_News": "ary_videos"
        }

        all_data = {}

        for channel_name, table_name in channels.items():
            cursor.execute(f"""
                SELECT title, channel_name, view_count FROM {table_name}
                WHERE channel_name = %s
                ORDER BY view_count DESC LIMIT 1
            """, (channel_name,))
            most_viewed = cursor.fetchone()

            cursor.execute(f"""
                SELECT title, channel_name, view_count FROM {table_name}
                WHERE channel_name = %s
                ORDER BY view_count ASC LIMIT 1
            """, (channel_name,))
            least_viewed = cursor.fetchone()

            cursor.execute(f"""
                SELECT title, channel_name, like_count FROM {table_name}
                WHERE channel_name = %s
                ORDER BY like_count DESC LIMIT 1
            """, (channel_name,))
            most_liked = cursor.fetchone()

            cursor.execute(f"""
                SELECT title, channel_name, like_count FROM {table_name}
                WHERE channel_name = %s
                ORDER BY like_count ASC LIMIT 1
            """, (channel_name,))
            least_liked = cursor.fetchone()

            all_data[channel_name] = {
                "most_viewed": most_viewed if most_viewed else ("No data", channel_name, 0),
                "least_viewed": least_viewed if least_viewed else  ("No data", channel_name, 0),
                "most_liked": most_liked if most_liked else  ("No data", channel_name, 0),
                "least_liked": least_liked if least_liked else  ("No data", channel_name, 0),
            }

        cursor.close()
        conn.close()

        return render_template("simple_stats.html", all_data=all_data)

    except Exception as e:
        return f"Database error: {e}"

@app.route('/download/<platform>')
def download_excel(platform):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Choose SQL query and sheet name based on platform
        if platform == 'facebook':
            cursor.execute("SELECT page_name, follower, likes, following FROM facebook_stats")
            columns = ['Page Name', 'Follower', 'Likes', 'Following']
            filename = 'facebook_stats.xlsx'
            sheet_name = 'Facebook Stats'
        elif platform == 'youtube':
            cursor.execute("SELECT name, subscribers, views, videos FROM youtube_stats")
            columns = ['Channel Name', 'Subscribers', 'Views', 'Videos']
            filename = 'youtube_stats.xlsx'
            sheet_name = 'YouTube Stats'
        elif platform == 'youtube_tags':
            cursor.execute("SELECT title, views, channel_name, link FROM youtube_tags")
            columns = ['title', 'views', 'channel_name', 'url']
            filename = 'youtube_tags.xlsx'
            sheet_name = 'YouTube tags'
        elif platform == 'youtube_tags1':
            cursor.execute("SELECT  views, channel_name, link FROM youtube_tags")
            columns = ['views', 'channel_name', 'url']
            filename = 'youtube_tags1.xlsx'
            sheet_name = 'YouTube tags1'
        elif platform == 'search-top-videos':
            cursor.execute("SELECT  views, title, channel, url FROM youtube_top_videos")
            columns = ['views', 'title','channel', 'url']
            filename = 'search_by_title.xlsx'
            sheet_name = 'YouTube title data' 

        elif platform == 'keyword_views':
            cursor.execute("SELECT  keyword, channel_name, views, start_date, end_date, search_time FROM keyword_views")
            columns = ['keyword', 'channel_name','views', 'start_date', 'end_date','search_time']
            filename = 'search_by_channel.xlsx'
            sheet_name = 'YouTube channel data' 
            
        elif platform == 'instagram':
            cursor.execute("SELECT page_name, followers, following, posts FROM instagram_stats")
            columns = ['Page Name', 'Followers', 'Following', 'Posts']
            filename = 'instagram_stats.xlsx'
            sheet_name = 'Instagram Stats'
            
        else:
            return "Invalid platform"

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        df = pd.DataFrame(rows, columns=columns)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        output.seek(0)

        return send_file(
            output,
            download_name=filename,
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return f"Download failed: {e}"







@app.route('/search-top-videos', methods=['GET', 'POST'])
def search_top_videos():
    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()

        if not keyword:
            return "Please enter a keyword.", 400

        # Default to last 3 days if no date provided
        try:
            if start_date:
                published_after = datetime.fromisoformat(start_date).astimezone(pytz.UTC).isoformat()
            else:
                published_after = (datetime.now(pytz.UTC) - timedelta(days=3)).isoformat()
        except ValueError:
            return "Invalid start date format.", 400

        try:
            search_params = {
                'q': keyword,
                'part': 'snippet',
                'type': 'video',
                'order': 'relevance',
                'maxResults': 25,
                'regionCode': 'PK',
                'publishedAfter': published_after
            }

            # Only add end date if provided
            if end_date:
                try:
                    search_params['publishedBefore'] = datetime.fromisoformat(end_date).astimezone(pytz.UTC).isoformat()
                except ValueError:
                    return "Invalid end date format.", 400

            search_response = youtube_key.search().list(**search_params).execute()

            video_ids = [item['id']['videoId'] for item in search_response['items']]
            if not video_ids:
                return f"No videos found for '{keyword}'.", 404

            video_response = youtube_key.videos().list(
                part=['snippet', 'statistics'],
                id=','.join(video_ids)
            ).execute()

            # videos = []
            # for item in video_response['items']:
            #     title = item['snippet']['title']
            #     channel = item['snippet']['channelTitle']
            #     views = int(item['statistics'].get('viewCount', 0))
            #     video_id = item['id']
            #     url = f"https://www.youtube.com/watch?v={video_id}"
            #     videos.append((views, title, channel, url))

            videos = []
            for item in video_response['items']:
                title = item['snippet']['title']
                channel = item['snippet']['channelTitle']
                view_count_raw = item['statistics'].get('viewCount', 0)
                try:
                    views = f"{int(view_count_raw):,}"
                except (ValueError, TypeError):
                    views = "N/A"
                video_id = item['id']
                url = f"https://www.youtube.com/watch?v={video_id}"
                videos.append((views, title, channel, url))

            videos.sort(reverse=True)

            # Send data to PostgreSQL
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM youtube_top_videos")
                for views, title, channel, url in videos:
                    cur.execute(
                        "INSERT INTO youtube_top_videos (views, title, channel, url, keyword, search_time) VALUES (%s, %s, %s, %s, %s, NOW())",
                        (views.replace(',', ''), title, channel, url, keyword)
                    )
                conn.commit()
                cur.close()
                conn.close()
            except Exception as db_error:
                print(f"Database error: {db_error}")

# ------------------
            return render_template('search_top_videos.html',
                                   videos=videos,
                                   keyword=keyword,
                                   start_date=start_date,
                                   end_date=end_date,
                                   error=None)

        except Exception as e:
            return f"Error during YouTube API call: {str(e)}", 500

    # GET method
    return render_template('search_top_videos.html',
                           videos=None,
                           keyword='',
                           start_date='',
                           end_date='',
                           error=None)





@app.route('/keyword_views', methods=['GET', 'POST'])
def keyword_views():
    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if not keyword:
            return render_template('keyword_views.html', channel_views=None, keyword='', error="Please enter a keyword.")

        if not start_date or not end_date:
            return render_template('keyword_views.html', channel_views=None, keyword='', error="Please select both start and end dates.")

        # Convert start and end dates to ISO format with 'Z' (UTC time)
        start_date = datetime.strptime(start_date, "%Y-%m-%d").replace(microsecond=0).isoformat() + 'Z'
        end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(microsecond=0).isoformat() + 'Z'

        published_after = start_date  # Use the start_date for the query

        channel_views = defaultdict(int)

        for channel_name, channel_id in channels_to_check.items():
            try:
                search_response = youtube_key.search().list(
                    q=keyword,
                    part='snippet',
                    type='video',
                    channelId=channel_id,
                    publishedAfter=published_after,
                    maxResults=50,
                    order='date'
                ).execute()

                video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                if video_ids:
                    video_response = youtube_key.videos().list(
                        part='snippet,statistics',
                        id=','.join(video_ids)
                    ).execute()

                    for item in video_response.get('items', []):
                        title = item['snippet']['title'].lower()
                        if keyword.lower() in title:
                            views = int(item['statistics'].get('viewCount', 0))
                            channel_views[channel_name] += views
            except Exception as e:
                print(f"Error processing channel {channel_name}: {e}")

        # Sort and render
        sorted_views = sorted(channel_views.items(), key=lambda x: x[1], reverse=True)

        # Save keyword views to PostgreSQL
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM keyword_views",
                (keyword, start_date, end_date)
            )
            for channel_name, views in sorted_views:
                cur.execute(
                    "INSERT INTO keyword_views (keyword, channel_name, views, start_date, end_date, search_time) VALUES (%s, %s, %s, %s, %s, NOW())",
                    (keyword, channel_name, views, start_date, end_date)
                )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as db_error:
            print(f"Database error: {db_error}")


        
        return render_template('keyword_views.html', channel_views=sorted_views, keyword=keyword, error=None)

    return render_template('keyword_views.html', channel_views=None, keyword='', error=None)







if __name__ == '__main__':
    app.run(debug=True,port=5001)
