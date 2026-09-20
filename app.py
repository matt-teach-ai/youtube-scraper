from flask import Flask, render_template, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/crawl', methods=['POST'])
def crawl():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL kanála je povinná.'}), 400

    # Ak ide o domovskú URL kanála, pridáme /videos pre získanie long-form videí
    if '@' in url and not url.endswith('/videos'):
        url = url.rstrip('/') + '/videos'
        
    # Ak ide o starší formát /c/ alebo /channel/, pridáme /videos
    if ('/c/' in url or '/channel/' in url or '/user/' in url) and not url.endswith('/videos'):
        url = url.rstrip('/') + '/videos'

    videos = []
    try:
        import yt_dlp
        
        # Nastavenia pre yt-dlp - získame až 290 videí z kanála (vyžaduje yt-dlp master branch)
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'quiet': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'playlistend': 290
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            if result and 'entries' in result:
                for entry in result['entries']:
                    if entry:
                        vid = entry.get('id')
                        if vid and len(vid) == 11:
                            videos.append(f"https://www.youtube.com/watch?v={vid}")
                            
        # Ak yt-dlp zlyhá (napríklad pre zmeny v YouTube API), použijeme záložný regex pre rýchlych ~30 videí
        if not videos:
            import urllib.request
            import re
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            html = urllib.request.urlopen(req).read().decode('utf-8')
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            unique_ids = list(dict.fromkeys(video_ids))
            videos = [f"https://www.youtube.com/watch?v={vid}" for vid in unique_ids]
            
        return jsonify({'videos': videos})
    except Exception as e:
        return jsonify({'error': f"Chyba na strane servera: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
