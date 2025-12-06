import threading
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image as PILImage
import json
from datetime import datetime
import detect_pipeline

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ForensicTool:
    """Wrapper for detect_pipeline to provide analyze_image interface"""
    def analyze_image(self, path):
        try:
            # The new detect_pipeline returns the exact structure we need
            return detect_pipeline.make_report(path)
        except Exception as e:
            print(f"Pipeline error: {e}")
            return {
                "file": path,
                "verdict": "Error",
                "score": 0,
                "flags": ["Analysis Failed"],
                "details": {}
            }

class ProForensicGUI(ctk.CTk):
    def __init__(self, backend=None):
        super().__init__()
        
        # Window setup - keeping it big for better view
        self.title("Forensic Analyzer Pro - Advanced Detection")
        self.geometry("1600x900")
        
        # My custom color palette - Dark theme looks professional
        self.c = {
            "bg": "#0d1117",        # Github-like dark background
            "card": "#161b22",      # Card background
            "sidebar": "#010409",   # Darker sidebar
            "cyan": "#58a6ff",      # Accent color
            "green": "#3fb950",     # Success
            "red": "#f85149",       # Danger/Fake
            "yellow": "#d29922",    # Warning
            "border": "#30363d",    # Subtle borders
            "blue": "#1f6feb",      # Info buttons
            "purple": "#8957e5"     # Extra features
        }
        
        self.configure(fg_color=self.c["bg"])
        
        # LOGIC HANDLER
        if backend:
            self.tool = backend
        else:
            self.tool = ForensicTool()

        self.current_path = None
        self.current_report = None
        
        # Start building the interface
        self.build_ui()
        
    def build_ui(self):
        # Using a 3-column layout:
        # 1. Sidebar (Controls)
        # 2. Results Panel (Left)
        # 3. Image Preview (Right)
        
        self.grid_columnconfigure(0, weight=0)  # Fixed sidebar
        self.grid_columnconfigure(1, weight=3)  # Results take more space
        self.grid_columnconfigure(2, weight=2)  # Image preview
        self.grid_rowconfigure(0, weight=1)
        
        self.create_sidebar()
        self.create_details_panel()
        self.create_image_panel()
        
    def create_sidebar(self):
        # Left sidebar for main buttons
        sidebar = ctk.CTkFrame(self, width=200, fg_color=self.c["sidebar"], corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False) # Stop it from shrinking
        
        # App Logo/Title
        ctk.CTkLabel(sidebar, text="🔬", font=("Arial", 45)).pack(pady=(30, 10))
        ctk.CTkLabel(
            sidebar,
            text="FORENSIC\nANALYZER",
            font=("Arial", 18, "bold"),
            text_color=self.c["cyan"]
        ).pack()
        ctk.CTkLabel(sidebar, text="Pro Edition", font=("Arial", 10), text_color="gray").pack(pady=(0, 40))
        
        # MAIN BUTTONS
        
        # 1. Upload Button
        self.btn_upload = ctk.CTkButton(
            sidebar,
            text="📂 UPLOAD",
            command=self.upload_image,
            height=50,
            font=("Arial", 14, "bold"),
            fg_color=self.c["cyan"],
            text_color="black",
            hover_color=self.c["green"]
        )
        self.btn_upload.pack(padx=15, pady=10, fill="x")
        
        # 2. Analyze Button (Disabled until image is loaded)
        self.btn_analyze = ctk.CTkButton(
            sidebar,
            text="⚡ ANALYZE",
            command=self.start_analysis,
            height=50,
            font=("Arial", 14, "bold"),
            fg_color=self.c["green"],
            text_color="black",
            state="disabled"
        )
        self.btn_analyze.pack(padx=15, pady=10, fill="x")
        
        # 3. Report Button (Enabled after analysis)
        self.btn_report = ctk.CTkButton(
            sidebar,
            text="📄 REPORT",
            command=self.show_report_section,
            height=50,
            font=("Arial", 14, "bold"),
            fg_color=self.c["blue"],
            text_color="white",
            state="disabled"
        )
        self.btn_report.pack(padx=15, pady=10, fill="x")
        
        # Dummy stats for look and feel
        stats_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        stats_frame.pack(pady=30, fill="x")
        
        ctk.CTkLabel(stats_frame, text="SYSTEM STATUS", font=("Arial", 9), text_color="gray").pack()
        ctk.CTkLabel(stats_frame, text="ONLINE", font=("Arial", 20, "bold"), text_color=self.c["green"]).pack()
        
    def create_details_panel(self):
        # Details on LEFT (column 1)
        self.details_panel = ctk.CTkScrollableFrame(self, fg_color=self.c["bg"])
        self.details_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 5), pady=10)
        
        # Header
        header = ctk.CTkFrame(self.details_panel, fg_color=self.c["card"], height=60)
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            header,
            text="📊 ANALYSIS RESULTS",
            font=("Arial", 16, "bold")
        ).pack(side="left", padx=20, pady=15)
        
        # Placeholder
        self.placeholder = ctk.CTkLabel(
            self.details_panel,
            text="No analysis yet\n\nUpload an image and click 'ANALYZE'",
            font=("Arial", 14),
            text_color="gray"
        )
        self.placeholder.pack(pady=100)
        
        # Report Panel (Hidden initially)
        self.report_panel = ctk.CTkFrame(self, fg_color=self.c["bg"])
        # Grid position will be set when shown
        
    def create_image_panel(self):
        # Image on RIGHT (column 2)
        self.img_panel = ctk.CTkFrame(self, fg_color=self.c["bg"])
        self.img_panel.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
        
        # Header
        header = ctk.CTkFrame(self.img_panel, fg_color=self.c["card"], height=60)
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="📸 IMAGE PREVIEW",
            font=("Arial", 16, "bold")
        ).pack(side="left", padx=20, pady=15)
        
        # Image container
        self.img_container = ctk.CTkFrame(self.img_panel, fg_color=self.c["card"])
        self.img_container.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Placeholder
        self.img_label = ctk.CTkLabel(
            self.img_container,
            text="No image loaded\n\nClick 'UPLOAD' to select an image",
            font=("Arial", 14),
            text_color="gray"
        )
        self.img_label.pack(expand=True)
        
    def upload_image(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.jpg *.png *.jpeg *.bmp *.tiff")]
        )
        if path:
            self.current_path = path
            self.display_image(path)
            self.btn_analyze.configure(state="normal")
            
    def display_image(self, path):
        try:
            img = PILImage.open(path)
            img.thumbnail((600, 600))
            
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            
            self.img_label.configure(image=photo, text="")
            self.img_label.image = photo
            
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load image: {e}")
            
    def start_analysis(self):
        if not self.current_path:
            return
            
        self.btn_analyze.configure(state="disabled", text="⏳ ANALYZING...")
        
        # Show loading
        for w in self.details_panel.winfo_children():
            if w != self.details_panel._parent_canvas:
                w.destroy()
                
        loading = ctk.CTkLabel(
            self.details_panel,
            text="⚡ Running forensic analysis...",
            font=("Arial", 16, "bold"),
            text_color=self.c["cyan"]
        )
        loading.pack(pady=100)
        
        threading.Thread(target=self.run_analysis, daemon=True).start()
        
    def run_analysis(self):
        try:
            report = self.tool.analyze_image(self.current_path)
            self.current_report = report
            self.after(0, lambda: self.display_results(report))
            self.after(0, lambda: self.btn_report.configure(state="normal"))
        except Exception as e:
            err_msg = str(e)
            print(f"Analysis error: {err_msg}")
            self.after(0, lambda msg=err_msg: messagebox.showerror("Error", msg))
        finally:
            self.after(0, lambda: self.btn_analyze.configure(state="normal", text="⚡ ANALYZE"))

    def show_dashboard(self):
        """Switch back to Dashboard View"""
        self.report_panel.grid_remove()
        self.details_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 5), pady=10)
        self.img_panel.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)

    def generate_report_text(self, report):
        """Generate text for report"""
        lines = []
        lines.append("="*60)
        lines.append(f"FORENSIC ANALYSIS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("="*60)
        lines.append(f"\nFILE: {os.path.basename(report.get('file', 'Unknown'))}")
        lines.append(f"VERDICT: {report.get('verdict', 'Unknown').upper()}")
        lines.append(f"THREAT SCORE: {report.get('score', 0)}%\n")
        
        lines.append("-" * 30)
        lines.append("1. SYNTHETIC PATTERN ANALYSIS")
        lines.append("-" * 30)
        ai = report.get("details", {}).get("ai_detection", {})
        lines.append(f"Status:      {ai.get('status', 'Unknown')}")
        lines.append(f"Confidence:  {ai.get('conf', 0)*100:.1f}%")
        lines.append(f"HF Ratio:    {ai.get('hf_ratio', 0):.4f}")
        if ai.get("reasons"):
            lines.append("Reasons:")
            for reason in ai.get("reasons", []):
                lines.append(f"  • {reason}")
        
        lines.append("\n" + "-" * 30)
        lines.append("2. COMPRESSION & QUALITY")
        lines.append("-" * 30)
        quant = report.get("details", {}).get("quantization", {})
        lines.append(f"Quality:     {quant.get('quality', 'Unknown')}")
        lines.append(f"Double Comp: {'YES' if quant.get('double_compressed') else 'NO'}")
        
        lines.append("\n" + "-" * 30)
        lines.append("3. ERROR LEVEL ANALYSIS (ELA)")
        lines.append("-" * 30)
        ela = report.get("details", {}).get("ela", {})
        lines.append(f"ELA Score:   {ela.get('score', 0):.4f}")
        lines.append(f"Verdict:     {'Suspicious' if ela.get('score', 0) > 0.15 else 'Normal'}")
        
        lines.append("\n" + "-" * 30)
        lines.append("4. METADATA ANALYSIS")
        lines.append("-" * 30)
        meta = report.get("details", {}).get("metadata", {})
        lines.append(f"Camera:      {meta.get('camera', 'None')}")
        lines.append(f"Software:    {meta.get('software', 'None')}")
        lines.append(f"EXIF Data:   {'Present' if meta.get('has_exif') else 'Missing'}")
        
        lines.append("\n" + "-" * 30)
        lines.append("5. DETECTED FLAGS")
        lines.append("-" * 30)
        flags = report.get("flags", [])
        if flags:
            for flag in flags:
                lines.append(f"• {flag}")
        else:
            lines.append("No specific flags detected.")
            
        lines.append("\n" + "="*60)
        lines.append("END OF REPORT")
        lines.append("="*60)
        return "\n".join(lines)

    def show_report_section(self):
        """Switch to Report View"""
        if not self.current_report:
            messagebox.showwarning("No Data", "Please analyze an image first.")
            return
            
        try:
            # Hide Dashboard
            self.details_panel.grid_remove()
            self.img_panel.grid_remove()
            
            # Show Report Panel
            self.report_panel.grid(row=0, column=1, columnspan=2, sticky="nsew", padx=10, pady=10)
            
            # Clear previous report
            for widget in self.report_panel.winfo_children():
                widget.destroy()
                
            # Header
            header = ctk.CTkFrame(self.report_panel, fg_color=self.c["card"], height=60)
            header.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(
                header,
                text="📄 FULL FORENSIC REPORT",
                font=("Arial", 18, "bold")
            ).pack(side="left", padx=20, pady=15)
            
            ctk.CTkButton(
                header,
                text="⬅ BACK TO DASHBOARD",
                command=self.show_dashboard,
                fg_color=self.c["bg"],
                text_color="white",
                border_width=1,
                border_color="gray"
            ).pack(side="right", padx=20)
            
            # Report Content
            report_text = self.generate_report_text(self.current_report)
            
            textbox = ctk.CTkTextbox(self.report_panel, font=("Consolas", 14))
            textbox.pack(fill="both", expand=True, padx=20, pady=10)
            textbox.insert("1.0", report_text)
            textbox.configure(state="disabled")
            
            # Save Button
            ctk.CTkButton(
                self.report_panel, 
                text="💾 SAVE REPORT TO FILE",
                command=lambda: self.save_report_to_file(report_text),
                fg_color=self.c["green"],
                height=40,
                font=("Arial", 14, "bold")
            ).pack(pady=20)
            
        except Exception as e:
            messagebox.showerror("Report Error", f"Failed to generate report: {str(e)}")
            self.show_dashboard()

    def save_report_to_file(self, text):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text File", "*.txt")])
        if path:
            with open(path, "w") as f:
                f.write(text)
            messagebox.showinfo("Saved", "Report saved successfully!")

    def display_results(self, r):
        try:
            # Clear
            for w in self.details_panel.winfo_children():
                if w != self.details_panel._parent_canvas:
                    w.destroy()
                    
            # Verdict Banner
            verdict = r.get("verdict", "Unknown")
            score = r.get("score", 0)
            
            if "Fake" in verdict:
                v_col = self.c["red"]
            elif "Suspicious" in verdict:
                v_col = self.c["yellow"]
            else:
                v_col = self.c["green"]
                
            verdict_card = ctk.CTkFrame(self.details_panel, fg_color=v_col, height=100)
            verdict_card.pack(fill="x", pady=(0, 15))
            
            ctk.CTkLabel(
                verdict_card,
                text=verdict.upper(),
                font=("Arial", 28, "bold"),
                text_color="black" if v_col != self.c["red"] else "white"
            ).pack(pady=(20, 5))
            
            ctk.CTkLabel(
                verdict_card,
                text=f"Threat Score: {score}%",
                font=("Arial", 14, "bold"),
                text_color="black" if v_col != self.c["red"] else "white"
            ).pack(pady=(0, 20))
            
            details = r.get("details", {})
            
            # AI Detection Card
            ai = details.get("ai_detection", {})
            ai_status = ai.get("status", "Unknown").upper()
            is_ai = ai.get("ai_gen")
            
            self.create_card(
                "🤖 SYNTHETIC PATTERN ANALYSIS",
                [
                    ("Status", ai_status),
                    ("Confidence", f"{ai.get('conf', 0)*100:.1f}%"),
                    ("HF Ratio", f"{ai.get('hf_ratio', 0):.3f}")
                ],
                is_ai or "SUSPICIOUS" in ai_status or "LIKELY" in ai_status
            )
            
            # Hugging Face API Card
            hf = details.get("huggingface_api", {})
            if hf.get("api_available") and hf.get("classifications"):
                hf_items = [
                    ("API Status", "✓ ONLINE (FREE)"),
                    ("Model", "AI-image-detector"),
                    ("AI Detection", "YES" if hf.get("ai_generated") else "NO"),
                    ("Confidence", f"{hf.get('confidence', 0)*100:.1f}%"),
                ]
                classifications = hf.get("classifications", [])
                if classifications:
                    hf_items.append(("", ""))
                    hf_items.append(("Classifications:", ""))
                    for cls in classifications:
                        label = cls['name'].title()
                        hf_items.append((f"  • {label}", cls['percentage']))
                self.create_card("🤗 HUGGING FACE MODEL (ML)", hf_items, hf.get("ai_generated"))
            
            # ELA Analysis Card
            ela = details.get("ela", {})
            self.create_card(
                "🔬 ERROR LEVEL ANALYSIS",
                [
                    ("ELA Score", f"{ela.get('score', 0):.4f}"),
                    ("Threshold", "0.15"),
                    ("Status", "Suspicious" if ela.get('score', 0) > 0.15 else "Normal")
                ],
                ela.get('score', 0) > 0.15
            )
            
            # Compression Card
            quant = details.get("quantization", {})
            self.create_card(
                "📊 COMPRESSION",
                [
                    ("JPEG Quality", f"{quant.get('quality', 'N/A')}%"),
                    ("Double Compressed", "YES" if quant.get('double_compressed') else "NO")
                ],
                quant.get('double_compressed')
            )
            
            # Clone Detection Card - REMOVED
            # clone = details.get("clones", {})
            # self.create_card(...)
            
            # Face Analysis Card - REMOVED
            # face = details.get("faces", {})
            # self.create_card(...)
            
            # Lighting Card
            light = details.get("lighting", {})
            self.create_card(
                "💡 LIGHTING",
                [
                    ("Consistency", "OK" if light.get('consistent', True) else "INCONSISTENT"),
                    ("Variance", f"{light.get('variance', 0):.4f}")
                ],
                not light.get('consistent', True)
            )
            
            # Flags
            flags = r.get("flags", [])
            if flags:
                flag_card = ctk.CTkFrame(self.details_panel, fg_color=self.c["card"], border_width=2, border_color=self.c["red"])
                flag_card.pack(fill="x", pady=10)
                
                ctk.CTkLabel(
                    flag_card,
                    text="⚠️ DETECTED ISSUES",
                    font=("Arial", 14, "bold"),
                    text_color=self.c["red"]
                ).pack(anchor="w", padx=15, pady=(15, 10))
                
                for flag in flags:
                    ctk.CTkLabel(
                        flag_card,
                        text=f"▸ {flag}",
                        font=("Arial", 12),
                        anchor="w"
                    ).pack(anchor="w", padx=20, pady=2)
                ctk.CTkLabel(flag_card, text="").pack(pady=5)
                
            # Actions
            btn_frame = ctk.CTkFrame(self.details_panel, fg_color="transparent")
            btn_frame.pack(pady=20)
            
            ela_path = ela.get("ela_path", "")
            if ela_path and os.path.exists(ela_path):
                ctk.CTkButton(
                    btn_frame,
                    text="View ELA Image",
                    command=lambda: os.startfile(ela_path),
                    fg_color=self.c["cyan"],
                    text_color="black"
                ).pack(fill="x", pady=5)

            noise = details.get("noise", {})
            noise_path = noise.get("noise_map", "")
            if noise_path and os.path.exists(noise_path):
                ctk.CTkButton(
                    btn_frame,
                    text="View Noise Map",
                    command=lambda: os.startfile(noise_path),
                    fg_color="#FF5500", # Orange for visibility
                    text_color="white"
                ).pack(fill="x", pady=5)
                
            meta = details.get("metadata", {})
            if meta.get("gps_link"):
                ctk.CTkButton(
                    btn_frame,
                    text="Open GPS Location",
                    command=lambda: os.startfile(meta["gps_link"]),
                    fg_color=self.c["green"],
                    text_color="black"
                ).pack(fill="x", pady=5)
                
            raw_tags = meta.get("raw_tags", {})
            if raw_tags:
                ctk.CTkButton(
                    btn_frame,
                    text="📄 View Full Metadata",
                    command=lambda: self.show_full_metadata(raw_tags),
                    fg_color=self.c["purple"],
                    text_color="white"
                ).pack(fill="x", pady=5)
                
            ctk.CTkButton(
                btn_frame,
                text="📊 View Professional Report",
                command=self.show_report_section,
                fg_color=self.c["blue"],
                text_color="white"
            ).pack(fill="x", pady=5)
            
        except Exception as e:
            messagebox.showerror("Display Error", f"Error displaying results: {str(e)}")
            print(f"Display Error: {e}")

    def create_card(self, title, items, is_alert=False):
        try:
            border_col = self.c["red"] if is_alert else self.c["border"]
            
            card = ctk.CTkFrame(
                self.details_panel,
                fg_color=self.c["card"],
                border_width=1,
                border_color=border_col
            )
            card.pack(fill="x", pady=8)
            
            ctk.CTkLabel(
                card,
                text=title,
                font=("Arial", 13, "bold"),
                anchor="w"
            ).pack(fill="x", padx=15, pady=(12, 8))
            
            for label, value in items:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=2)
                
                ctk.CTkLabel(
                    row,
                    text=f"{label}:",
                    font=("Arial", 11),
                    text_color="gray",
                    width=120,
                    anchor="w"
                ).pack(side="left")
                
                val_str = str(value)
                val_upper = val_str.upper()
                
                # Simplified alert check
                is_bad = is_alert and any(x in val_upper for x in ["YES", "DETECTED", "SUSPICIOUS", "INCONSISTENT", "AI-GENERATED"])
                val_col = self.c["red"] if is_bad else "white"
                
                ctk.CTkLabel(
                    row,
                    text=val_str,
                    font=("Arial", 11, "bold"),
                    text_color=val_col,
                    anchor="w"
                ).pack(side="left", fill="x", expand=True)
                
            ctk.CTkLabel(card, text="").pack(pady=5)
        except Exception as e:
            print(f"Card Error ({title}): {e}")

    def show_full_metadata(self, tags):
        """Show full EXIF metadata in a popup with download option"""
        if hasattr(self, 'meta_win') and self.meta_win is not None and self.meta_win.winfo_exists():
            self.meta_win.lift()
            return

        self.meta_win = ctk.CTkToplevel(self)
        self.meta_win.title("Full EXIF Metadata")
        self.meta_win.geometry("600x600")
        self.meta_win.attributes("-topmost", True) # Keep on top
        
        # Scrollable Text
        textbox = ctk.CTkTextbox(self.meta_win, font=("Consolas", 12))
        textbox.pack(fill="both", expand=True, padx=20, pady=(20, 10))
        
        json_str = json.dumps(tags, indent=2)
        textbox.insert("1.0", json_str)
        textbox.configure(state="disabled")
        
        # Download Button
        def save_meta():
            try:
                path = ctk.filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("Text files", "*.txt")],
                    initialfile="metadata.json"
                )
                if path:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(json_str)
                    messagebox.showinfo("Saved", f"Metadata saved to {path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

        ctk.CTkButton(
            self.meta_win,
            text="💾 Download Metadata",
            command=save_meta,
            fg_color=self.c["green"],
            text_color="black"
        ).pack(pady=(0, 20))

if __name__ == "__main__":
    app = ProForensicGUI()
    app.mainloop()
