import customtkinter as ctk
import threading
import json
import time
import os
import sys
from PIL import Image

# Import the engine
import crawler_engine

# Configuration
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Bitflow Nova - Website Intelligence")
        self.geometry("1100x800")
        
        try:
            self.iconbitmap("logo.ico") # Only works if .ico exists, skipping safely
        except:
            pass

        # Layout configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        # Logo
        try:
            # Load and display logo
            self.logo_img = ctk.CTkImage(Image.open("logo.jpeg"), size=(100, 100))
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="", image=self.logo_img)
            self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
            
            self.title_label = ctk.CTkLabel(self.sidebar_frame, text="Bitflow Nova", font=ctk.CTkFont(size=18, weight="bold"))
            self.title_label.grid(row=1, column=0, padx=20, pady=(0, 20))
        except Exception as e:
            print(f"Logo error: {e}")
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Bitflow Nova", font=ctk.CTkFont(size=20, weight="bold"))
            self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Nav Buttons
        self.sidebar_button_dashboard = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard)
        self.sidebar_button_dashboard.grid(row=2, column=0, padx=20, pady=10)
        
        self.sidebar_button_seo = ctk.CTkButton(self.sidebar_frame, text="SEO Analysis", command=self.show_seo)
        self.sidebar_button_seo.grid(row=3, column=0, padx=20, pady=10)

        self.sidebar_button_security = ctk.CTkButton(self.sidebar_frame, text="Security", command=self.show_security)
        self.sidebar_button_security.grid(row=4, column=0, padx=20, pady=10)
        
        self.sidebar_button_pages = ctk.CTkButton(self.sidebar_frame, text="Pages Found", command=self.show_pages)
        self.sidebar_button_pages.grid(row=5, column=0, padx=20, pady=10)

        self.sidebar_button_files = ctk.CTkButton(self.sidebar_frame, text="Files & Media", command=self.show_files)
        self.sidebar_button_files.grid(row=6, column=0, padx=20, pady=10, sticky="n")

        # Main Content Area
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Dashboard View (Default)
        self.setup_dashboard()
        self.setup_seo_view()
        self.setup_security_view()
        self.setup_pages_view()
        self.setup_files_view()

        # Hide others initially
        self.hide_layers()
        self.frame_dashboard.grid(row=0, column=0, sticky="nsew")

        self.crawler_id = None
        self.is_running = False

    def hide_layers(self):
        self.frame_dashboard.grid_forget()
        self.frame_seo.grid_forget()
        self.frame_security.grid_forget()
        self.frame_pages.grid_forget()
        self.frame_files.grid_forget()

    def setup_dashboard(self):
        self.frame_dashboard = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frame_dashboard.grid_columnconfigure(0, weight=1)

        # Input Area
        self.url_var = ctk.StringVar(value="https://")
        self.url_entry = ctk.CTkEntry(self.frame_dashboard, textvariable=self.url_var, placeholder_text="Enter website URL", width=400)
        self.url_entry.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.btn_start = ctk.CTkButton(self.frame_dashboard, text="Start Analysis", command=self.start_crawl_thread)
        self.btn_start.grid(row=0, column=1, padx=20, pady=(20, 10))

        # Progress
        self.progress_bar = ctk.CTkProgressBar(self.frame_dashboard)
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.frame_dashboard, text="Ready to scan")
        self.status_label.grid(row=2, column=0, columnspan=2, padx=20, pady=5)

        # Stats Area
        self.stats_frame = ctk.CTkFrame(self.frame_dashboard)
        self.stats_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=20, sticky="nsew")
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.stat_pages = self.create_stat_card(self.stats_frame, "Pages Scanned", "0", 0, 0)
        self.stat_health = self.create_stat_card(self.stats_frame, "Health Score", "-", 0, 1)
        self.stat_issues = self.create_stat_card(self.stats_frame, "Total Issues", "0", 0, 2)

    def create_stat_card(self, parent, title, value, row, col):
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        lbl_title = ctk.CTkLabel(card, text=title, font=("Arial", 12))
        lbl_title.pack(pady=(10, 0))
        lbl_val = ctk.CTkLabel(card, text=value, font=("Arial", 24, "bold"))
        lbl_val.pack(pady=(0, 10))
        return lbl_val

    def setup_seo_view(self):
        self.frame_seo = ctk.CTkScrollableFrame(self.main_frame, label_text="SEO Issues")
    
    def setup_security_view(self):
        self.frame_security = ctk.CTkScrollableFrame(self.main_frame, label_text="Security Report")
        
    def setup_pages_view(self):
        self.frame_pages = ctk.CTkScrollableFrame(self.main_frame, label_text="Discovered Pages")
        
    def setup_files_view(self):
        self.frame_files = ctk.CTkScrollableFrame(self.main_frame, label_text="Extracted Media & Files")

    def show_dashboard(self):
        self.hide_layers()
        self.frame_dashboard.grid(row=0, column=0, sticky="nsew")

    def show_seo(self):
        self.hide_layers()
        self.frame_seo.grid(row=0, column=0, sticky="nsew")

    def show_security(self):
        self.hide_layers()
        self.frame_security.grid(row=0, column=0, sticky="nsew")

    def show_pages(self):
        self.hide_layers()
        self.frame_pages.grid(row=0, column=0, sticky="nsew")
        
    def show_files(self):
        self.hide_layers()
        self.frame_files.grid(row=0, column=0, sticky="nsew")

    def start_crawl_thread(self):
        if self.is_running: return
        url = self.url_var.get()
        if not url: return
        self.is_running = True
        self.btn_start.configure(state="disabled", text="Running...")
        self.progress_bar.set(0)
        t = threading.Thread(target=self.run_crawl, args=(url,), daemon=True)
        t.start()
        threading.Thread(target=self.monitor_crawl, daemon=True).start()

    def run_crawl(self, url):
        try:
            output_dir = os.path.join(os.getcwd(), 'crawler_output')
            os.makedirs(output_dir, exist_ok=True)
            self.crawler_id = crawler_engine.start_crawl(url, 2, output_dir)
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
            self.is_running = False

    def monitor_crawl(self):
        while self.is_running:
            time.sleep(1)
            if not self.crawler_id: continue
            try:
                status_json = crawler_engine.get_status(self.crawler_id)
                status = json.loads(status_json)
                if status.get('status') == 'not_found': continue

                pages = status.get('pages_crawled', 0)
                total = status.get('pages_total', 1)
                
                self.stat_pages.configure(text=str(pages))
                self.status_label.configure(text=f"Status: {status.get('status')} | Scanning: {status.get('current_url', '')}")
                if total > 0: self.progress_bar.set(pages / total if total > 20 else pages/20)

                if status.get('status') in ['completed', 'failed', 'error']:
                    self.is_running = False
                    self.load_results()
                    self.btn_start.configure(state="normal", text="Start Analysis")
                    self.status_label.configure(text=f"Finished: {status.get('status')}")
            except Exception as e:
                print(f"Monitor error: {e}")

    def load_results(self):
        output_dir = os.path.join(os.getcwd(), 'crawler_output')
        report_json = crawler_engine.get_analysis_report(self.crawler_id, output_dir)
        files_json = crawler_engine.get_files(self.crawler_id, output_dir)
        
        report = json.loads(report_json)
        files = json.loads(files_json)

        # Health Score (Simple calculation logic matched from Android)
        seo_count = len(report.get('seo_issues', []))
        sec_count = len(report.get('security_issues', []))
        ssl_valid = report.get('ssl', {}).get('valid', False)
        
        score = 100
        score -= min(seo_count * 2, 30)
        score -= min(sec_count * 3, 30)
        if not ssl_valid: score -= 20
        score = max(0, score)
        
        self.stat_health.configure(text=str(score))
        if score > 80: self.stat_health.configure(text_color="green")
        elif score > 50: self.stat_health.configure(text_color="orange")
        else: self.stat_health.configure(text_color="red")
        
        self.stat_issues.configure(text=str(seo_count + sec_count))

        # SEO Tab
        for w in self.frame_seo.winfo_children(): w.destroy()
        if not report.get('seo_issues'):
            ctk.CTkLabel(self.frame_seo, text="No SEO Issues Found!", text_color="green", font=("Arial", 16)).pack(pady=20)
        else:
            for issue in report['seo_issues']:
                self.create_issue_card(self.frame_seo, issue['url'], issue['issue'], "orange")

        # Security Tab
        for w in self.frame_security.winfo_children(): w.destroy()
        ssl = report.get('ssl')
        if ssl:
            color = "green" if ssl.get('valid') else "red"
            text = "SSL Valid" if ssl.get('valid') else "SSL Invalid"
            card = ctk.CTkFrame(self.frame_security)
            card.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(card, text=text, text_color=color, font=("Arial", 16, "bold")).pack(pady=10)
            if ssl.get('issuer'): ctk.CTkLabel(card, text=f"Issuer: {ssl['issuer']}").pack()
        
        if report.get('hidden_paths'):
            ctk.CTkLabel(self.frame_security, text=f"Hidden Paths ({len(report['hidden_paths'])})", font=("Arial", 14, "bold")).pack(pady=(10,5))
            for path in report['hidden_paths']:
                self.create_issue_card(self.frame_security, path['path'], f"Status: {path['status']}", "#6366F1")

        if report.get('security_issues'):
            ctk.CTkLabel(self.frame_security, text="Security Issues", font=("Arial", 14, "bold")).pack(pady=(10,5))
            for issue in report['security_issues']:
                self.create_issue_card(self.frame_security, issue['url'], issue['issue'], "red")

        # Pages Tab
        for w in self.frame_pages.winfo_children(): w.destroy()
        all_pages = report.get('all_pages', [])
        ctk.CTkLabel(self.frame_pages, text=f"Total Pages: {len(all_pages)}", font=("Arial", 14, "bold")).pack(pady=10)
        for page in all_pages:
            self.create_issue_card(self.frame_pages, page['url'], f"Status: {page['status']} | Time: {page['load_time']}ms", "white")

        # Files Tab
        for w in self.frame_files.winfo_children(): w.destroy()
        
        self.add_file_section("Images", files.get('images', []))
        self.add_file_section("Documents", files.get('documents', []))
        self.add_file_section("Scripts", files.get('scripts', []))
        self.add_file_section("Stylesheets", files.get('stylesheets', []))

    def add_file_section(self, title, file_list):
        if not file_list: return
        ctk.CTkLabel(self.frame_files, text=f"{title} ({len(file_list)})", font=("Arial", 14, "bold")).pack(pady=(10,5), anchor="w", padx=10)
        for f in file_list[:20]: # Limit to 20
            lbl = ctk.CTkLabel(self.frame_files, text=f"📄 {f}", anchor="w")
            lbl.pack(fill="x", padx=20, pady=2)
        if len(file_list) > 20:
             ctk.CTkLabel(self.frame_files, text=f"...and {len(file_list)-20} more", text_color="gray").pack()

    def create_issue_card(self, parent, url, text, color):
        card = ctk.CTkFrame(parent)
        card.pack(fill="x", padx=10, pady=5)
        # Text wrapping
        ctk.CTkLabel(card, text=text, text_color=color, font=("Arial", 12, "bold"), wraplength=500, justify="left").pack(anchor="w", padx=10, pady=(5,0))
        ctk.CTkLabel(card, text=url, text_color="gray", font=("Arial", 10), wraplength=500, justify="left").pack(anchor="w", padx=10, pady=(0,5))

if __name__ == "__main__":
    app = App()
    app.mainloop()
