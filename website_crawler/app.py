import os
import uuid
import threading
import json
import asyncio
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from crawler import AsyncCrawler
from database import DatabaseManager

app = Flask(__name__)
app.config['OUTPUT_FOLDER'] = os.path.abspath('output')
app.config['DB_FILE'] = os.path.join(app.config['OUTPUT_FOLDER'], 'crawler.db')

# Ensure output directory exists
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Initialize DB
db = DatabaseManager(app.config['DB_FILE'])

# Active Crawler Instances (InMemory for control)
active_crawlers_objs = {}

def run_async_crawler(crawl_id, output_dir, config):
    """Wrapper to run async crawler in a thread"""
    try:
        # Re-init DB connection inside thread if needed, but Manager handles it
        crawler = AsyncCrawler(crawl_id, output_dir, db, config)
        active_crawlers_objs[crawl_id] = crawler
        
        # Determine if we are resuming or starting?
        # The crawler itself just looks at DB queue. 
        # But we need to update status to running if not already.
        db.update_crawl_status(crawl_id, 'running')
        
        asyncio.run(crawler.run())
        
    except Exception as e:
        print(f"Crawler Thread Error: {e}")
        db.update_crawl_status(crawl_id, 'failed')
    finally:
        if crawl_id in active_crawlers_objs:
            del active_crawlers_objs[crawl_id]

@app.route('/')
def index():
    history = db.get_all_crawls()
    return render_template('index.html', history=history)

@app.route('/crawl', methods=['POST'])
def start_crawl():
    url = request.form.get('url')
    if not url:
        return "URL required", 400
        
    depth = int(request.form.get('depth', 1))
    
    # Advanced Config
    config = {
        'depth': depth,
        'concurrency': int(request.form.get('concurrency', 3)),
        'delay': float(request.form.get('delay', 1.0)),
        'proxy': request.form.get('proxy') or None,
        'user_agent_strategy': request.form.get('user_agent_strategy', 'random'),
        'allow_regex': request.form.get('allow_regex') or None,
        'deny_regex': request.form.get('deny_regex') or None
    }
    
    crawl_id = str(uuid.uuid4())
    db.create_crawl(crawl_id, url, depth, config)
    
    # Start Thread
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], crawl_id)
    thread = threading.Thread(target=run_async_crawler, args=(crawl_id, output_dir, config))
    thread.start()
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'crawl_id': crawl_id, 'status': 'pending'})

    return redirect(url_for('report', crawl_id=crawl_id))

@app.route('/report/<crawl_id>')
def report(crawl_id):
    crawl = db.get_crawl(crawl_id)
    if not crawl:
        return "Crawl not found", 404
    
    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], crawl_id)
    
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

    return render_template('report.html', crawl_id=crawl_id, files=files, crawl=crawl)

@app.route('/status/<crawl_id>')
def status(crawl_id):
    data = db.get_crawl_status(crawl_id)
    if not data:
        return jsonify({'status': 'not_found'})
        
    # Add pending count
    pending = db.get_pending_count(crawl_id)
    return jsonify({'status': data['status'], 'pending_queue': pending})

@app.route('/control/<crawl_id>/<action>', methods=['POST'])
def control_crawl(crawl_id, action):
    # Check if active
    crawler = active_crawlers_objs.get(crawl_id)
    
    if action == 'pause':
        if crawler: crawler.pause()
        db.update_crawl_status(crawl_id, 'paused')
        
    elif action == 'resume':
        if crawler:
            crawler.resume()
            db.update_crawl_status(crawl_id, 'running')
        else:
            # Cold Resume (Restart process)
            crawl_info = db.get_crawl_status(crawl_id)
            if crawl_info and crawl_info['status'] != 'running':
                output_dir = os.path.join(app.config['OUTPUT_FOLDER'], crawl_id)
                config = crawl_info.get('config', {})
                thread = threading.Thread(target=run_async_crawler, args=(crawl_id, output_dir, config))
                thread.start()
                
    elif action == 'stop':
        if crawler: crawler.stop()
        # Status update handled by thread exit
        
    return jsonify({'success': True})

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
