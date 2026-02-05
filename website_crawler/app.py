import os
import uuid
import threading
import json
import time
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from crawler import Crawler

app = Flask(__name__)
app.config['OUTPUT_FOLDER'] = os.path.abspath('output')
app.config['HISTORY_FILE'] = os.path.join(app.config['OUTPUT_FOLDER'], 'crawls.json')

# Ensure output directory exists
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store crawler *objects* in memory to control them
# Key: crawl_id, Value: Crawler instance
active_crawlers_objs = {}

# Crawl Metadata (Loaded from JSON)
crawl_history = {}

def load_history():
    global crawl_history
    if os.path.exists(app.config['HISTORY_FILE']):
        with open(app.config['HISTORY_FILE'], 'r') as f:
            crawl_history = json.load(f)
    else:
        crawl_history = {}

def save_history():
    with open(app.config['HISTORY_FILE'], 'w') as f:
        json.dump(crawl_history, f, indent=4)

# Load immediately on start
load_history()

def run_crawler(crawl_id, url, depth):
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], crawl_id)
    
    # Create Crawler Instance
    crawler = Crawler(url, output_dir, depth)
    active_crawlers_objs[crawl_id] = crawler
    
    # Update Status
    crawl_history[crawl_id]['status'] = 'running'
    save_history()
    
    try:
        crawler.run()
        if crawler.stopped:
             crawl_history[crawl_id]['status'] = 'stopped'
        else:
             crawl_history[crawl_id]['status'] = 'completed'
    except Exception as e:
        crawl_history[crawl_id]['status'] = 'failed'
        crawl_history[crawl_id]['error'] = str(e)
    finally:
        save_history()
        # Clean up object reference to free memory, but keep metadata
        if crawl_id in active_crawlers_objs:
            del active_crawlers_objs[crawl_id]

@app.route('/')
def index():
    # Sort history by date (newest first) - assuming insertion order or we could add timestamp
    # We'll just pass the dict items
    return render_template('index.html', history=crawl_history)

@app.route('/crawl', methods=['POST'])
def start_crawl():
    url = request.form.get('url')
    depth = int(request.form.get('depth', 1))
    
    crawl_id = str(uuid.uuid4())
    crawl_history[crawl_id] = {
        'id': crawl_id,
        'url': url,
        'depth': depth,
        'status': 'pending',
        'timestamp': time.time(),
        'output_dir': os.path.join(app.config['OUTPUT_FOLDER'], crawl_id)
    }
    save_history()
    
    thread = threading.Thread(target=run_crawler, args=(crawl_id, url, depth))
    thread.start()
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'crawl_id': crawl_id, 'status': 'pending'})

    return redirect(url_for('report', crawl_id=crawl_id))

@app.route('/report/<crawl_id>')
def report(crawl_id):
    if crawl_id not in crawl_history:
        return "Crawl not found", 404
        
    crawl_data = crawl_history[crawl_id]
    output_dir = crawl_data['output_dir']
    
    # Collect generated files
    files = {'content': [], 'images': [], 'documents': []}
    
    if os.path.exists(output_dir):
        content_dir = os.path.join(output_dir, 'content')
        if os.path.exists(content_dir):
            files['content'] = [f for f in os.listdir(content_dir) if f.endswith('.md')]
            
        images_dir = os.path.join(output_dir, 'images')
        if os.path.exists(images_dir):
            files['images'] = os.listdir(images_dir)
            
        docs_dir = os.path.join(output_dir, 'documents')
        if os.path.exists(docs_dir):
            files['documents'] = os.listdir(docs_dir)

    if request.headers.get('Accept') == 'application/json':
        return jsonify({'crawl': crawl_data, 'files': files})

    return render_template('report.html', crawl=crawl_data, crawl_id=crawl_id, files=files)

@app.route('/status/<crawl_id>')
def status(crawl_id):
    if crawl_id not in crawl_history:
        return jsonify({'status': 'not_found'})
    return jsonify(crawl_history[crawl_id])

@app.route('/control/<crawl_id>/<action>', methods=['POST'])
def control_crawl(crawl_id, action):
    if crawl_id not in active_crawlers_objs:
        return jsonify({'success': False, 'message': 'Crawler not active or finished'}), 400
    
    crawler = active_crawlers_objs[crawl_id]
    
    if action == 'pause':
        crawler.pause()
        crawl_history[crawl_id]['status'] = 'paused'
    elif action == 'resume':
        crawler.resume()
        crawl_history[crawl_id]['status'] = 'running'
    elif action == 'stop':
        crawler.stop()
        # Status update happens in the thread finally block or after run()
    
    save_history()
    return jsonify({'success': True, 'status': crawl_history[crawl_id]['status']})

@app.route('/download/<crawl_id>/<file_type>/<filename>')
def download_file(crawl_id, file_type, filename):
    folder_map = {
        'content': 'content',
        'image': 'images',
        'document': 'documents'
    }
    
    if file_type not in folder_map:
        return "Invalid file type", 400
        
    directory = os.path.join(app.config['OUTPUT_FOLDER'], crawl_id, folder_map[file_type])
    return send_from_directory(directory, filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
