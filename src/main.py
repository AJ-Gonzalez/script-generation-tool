"""
AI Mechanic Script Generation Tool
Main GUI application using CustomTKinter
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import threading
import time
import re
import os
import json
from pathlib import Path
from market_tools import (
    generate_comprehensive_topic_report,
    search_youtube_videos,
    extract_title_patterns,
    analyze_video_topics,
    analyze_video_content_with_llm
)
from script_generator import generate_script_with_llm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set appearance mode and color theme
ctk.set_appearance_mode("light")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class AIScriptGeneratorApp:
    def __init__(self):
        # Create main window
        self.root = ctk.CTk()
        self.root.title("The AI Mechanic - Script Generation Tool")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configure custom colors
        self.colors = {
            "bg_primary": "#FEFEFE",      # Very light warm white
            "bg_secondary": "#F8F6F3",    # Warm off-white
            "bg_card": "#FFFFFF",         # Pure white for cards
            "text_primary": "#2D3748",    # Dark gray for main text
            "text_secondary": "#464B54",  # Medium gray for secondary text
            "accent_teal": "#4FD1C7",     # Soft teal accent
            "accent_teal_hover": "#38B2AC", # Darker teal for hover
            "border_light": "#E2E8F0",    # Light border
            "success": "#68D391",         # Light green
            "warning": "#F6E05E",         # Light yellow
            "error": "#FC8181"            # Light red
        }
        
        # Configure the root window colors
        self.root.configure(fg_color=self.colors["bg_primary"])
        
        # API key management
        self.config_file = Path("config.json")
        self.api_key = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the main user interface"""
        
        # Main container
        main_container = ctk.CTkFrame(
            self.root,
            fg_color=self.colors["bg_primary"],
            corner_radius=0
        )
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(
            main_container,
            corner_radius=10,
            border_width=1,
            border_color=self.colors["border_light"],
            fg_color=self.colors["bg_card"],
            segmented_button_fg_color=self.colors["bg_secondary"],
            segmented_button_selected_color=self.colors["accent_teal"],
            segmented_button_selected_hover_color=self.colors["accent_teal_hover"],
            text_color=self.colors["text_primary"]
        )
        self.tabview.pack(fill="both", expand=True)
        
        # Create tabs with more spacing
        self.tab1 = self.tabview.add("  Script Generation  ")
        self.tab2 = self.tabview.add("  Research Panel  ") 
        self.tab3 = self.tabview.add("  Marketing Tools  ")
        self.tab4 = self.tabview.add("  API Settings  ")
        self.tab5 = self.tabview.add("  About  ")
        
        # Configure tab colors and setup placeholder content
        self.setup_script_generation_tab()
        self.setup_research_panel_tab()
        self.setup_marketing_tools_tab()
        self.setup_api_settings_tab()
        self.setup_analytics_tab()
        
    def setup_script_generation_tab(self):
        """Setup the script generation tab"""
        tab_frame = ctk.CTkFrame(
            self.tab1,
            fg_color=self.colors["bg_secondary"],
            corner_radius=15
        )
        tab_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Main scrollable container
        scroll_frame = ctk.CTkScrollableFrame(
            tab_frame,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            scroll_frame,
            text="Script Generation",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title_label.pack(pady=(0, 20))
        
        # Input fields container
        inputs_frame = ctk.CTkFrame(
            scroll_frame,
            fg_color=self.colors["bg_card"],
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border_light"]
        )
        inputs_frame.pack(fill="x", pady=(0, 20))
        
        # Topic input
        topic_label = ctk.CTkLabel(
            inputs_frame,
            text="Main Topic:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        topic_label.pack(fill="x", padx=20, pady=(20, 5))
        
        self.topic_input = ctk.CTkEntry(
            inputs_frame,
            placeholder_text="Enter the main topic for your video script",
            font=ctk.CTkFont(size=14),
            height=35,
            corner_radius=10,
            border_color=self.colors["border_light"],
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"]
        )
        self.topic_input.pack(fill="x", padx=20, pady=(0, 15))
        
        # Key points input
        keypoints_label = ctk.CTkLabel(
            inputs_frame,
            text="Key Points (use bullet points with - or * ):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        keypoints_label.pack(fill="x", padx=20, pady=(0, 5))
        
        self.keypoints_input = ctk.CTkTextbox(
            inputs_frame,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            corner_radius=10,
            height=120,
            wrap="word"
        )
        self.keypoints_input.pack(fill="x", padx=20, pady=(0, 15))
        self.keypoints_input.insert("0.0", "- Key point 1\n- Key point 2\n- Key point 3")
        
        # Brand details row
        brand_frame = ctk.CTkFrame(inputs_frame, fg_color="transparent")
        brand_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Brand name
        brand_left = ctk.CTkFrame(brand_frame, fg_color="transparent")
        brand_left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        brand_label = ctk.CTkLabel(
            brand_left,
            text="Brand Name:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        brand_label.pack(fill="x", pady=(0, 5))
        
        self.brand_input = ctk.CTkEntry(
            brand_left,
            placeholder_text="Your brand name",
            font=ctk.CTkFont(size=14),
            height=35,
            corner_radius=10,
            border_color=self.colors["border_light"],
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"]
        )
        self.brand_input.pack(fill="x")
        
        # Focus area
        focus_right = ctk.CTkFrame(brand_frame, fg_color="transparent")
        focus_right.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        focus_label = ctk.CTkLabel(
            focus_right,
            text="What We Focus On:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        focus_label.pack(fill="x", pady=(0, 5))
        
        self.focus_input = ctk.CTkEntry(
            focus_right,
            placeholder_text="What your brand focuses on",
            font=ctk.CTkFont(size=14),
            height=35,
            corner_radius=10,
            border_color=self.colors["border_light"],
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"]
        )
        self.focus_input.pack(fill="x")
        
        # Settings row
        settings_frame = ctk.CTkFrame(inputs_frame, fg_color="transparent")
        settings_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Tone selection
        tone_left = ctk.CTkFrame(settings_frame, fg_color="transparent")
        tone_left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tone_label = ctk.CTkLabel(
            tone_left,
            text="Tone:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        tone_label.pack(fill="x", pady=(0, 5))
        
        self.tone_input = ctk.CTkOptionMenu(
            tone_left,
            values=["Professional", "Casual", "Educational", "Conversational", "Energetic",],
            fg_color=self.colors["accent_teal"],
            button_color=self.colors["accent_teal_hover"],
            button_hover_color=self.colors["accent_teal"],
            dropdown_fg_color=self.colors["bg_card"],
            font=ctk.CTkFont(size=14)
        )
        self.tone_input.pack(fill="x")
        self.tone_input.set("Conversational")
        
        # Runtime
        runtime_right = ctk.CTkFrame(settings_frame, fg_color="transparent")
        runtime_right.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        runtime_label = ctk.CTkLabel(
            runtime_right,
            text="Target Runtime (minutes):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        runtime_label.pack(fill="x", pady=(0, 5))
        
        self.runtime_input = ctk.CTkEntry(
            runtime_right,
            placeholder_text="5",
            font=ctk.CTkFont(size=14),
            height=35,
            corner_radius=10,
            border_color=self.colors["border_light"],
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"]
        )
        self.runtime_input.pack(fill="x")
        self.runtime_input.insert(0, "5")
        
        # Generate button
        self.generate_button = ctk.CTkButton(
            scroll_frame,
            text="Generate Script Draft",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.colors["accent_teal"],
            hover_color=self.colors["accent_teal_hover"],
            corner_radius=25,
            height=45,
            width=200,
            command=self.generate_script
        )
        self.generate_button.pack(pady=20)
        
        # Preview area
        self.preview_frame = ctk.CTkFrame(
            scroll_frame,
            fg_color=self.colors["bg_card"],
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border_light"]
        )
        
        preview_title = ctk.CTkLabel(
            self.preview_frame,
            text="Script Preview",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        preview_title.pack(fill="x", padx=20, pady=(15, 5))
        
        self.preview_text = ctk.CTkTextbox(
            self.preview_frame,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            corner_radius=10,
            height=300,
            wrap="word"
        )
        self.preview_text.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.preview_text.insert("0.0", "Generated script will appear here...")
        self.preview_text.configure(state="disabled")
        
        # Action buttons frame
        buttons_frame = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.save_button = ctk.CTkButton(
            buttons_frame,
            text="Save as Markdown",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["success"],
            hover_color="#4299E1",
            corner_radius=20,
            height=35,
            width=150,
            command=self.save_script
        )
        self.save_button.pack(side="left", padx=(0, 10))
        
        self.copy_button = ctk.CTkButton(
            buttons_frame,
            text="Copy to Clipboard",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["warning"],
            hover_color="#E53E3E",
            corner_radius=20,
            height=35,
            width=150,
            command=self.copy_script
        )
        self.copy_button.pack(side="left")
        
        # Initially hide preview
        self.script_content = ""
        
    def setup_research_panel_tab(self):
        """Setup the research panel tab with dossier layout"""
        tab_frame = ctk.CTkFrame(
            self.tab2,
            fg_color=self.colors["bg_secondary"],
            corner_radius=15
        )
        tab_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Main container for the dossier layout
        main_container = ctk.CTkFrame(
            tab_frame,
            fg_color="transparent"
        )
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Two-column layout: main dossier content + articles sidebar
        dossier_columns = ctk.CTkFrame(
            main_container,
            fg_color="transparent"
        )
        dossier_columns.pack(fill="both", expand=True)
        
        # Left column - Main Research Dossier content (70% width)
        self.dossier_main = ctk.CTkFrame(
            dossier_columns,
            fg_color=self.colors["bg_card"],
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border_light"]
        )
        self.dossier_main.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Right column - Articles Referenced sidebar (30% width)
        self.articles_sidebar = ctk.CTkFrame(
            dossier_columns,
            fg_color=self.colors["bg_card"],
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border_light"],
            width=250
        )
        self.articles_sidebar.pack(side="right", fill="y", padx=(10, 0))
        self.articles_sidebar.pack_propagate(False)
        
        self.setup_dossier_content()
        self.setup_articles_sidebar()
        
        # Initially show placeholder message
        self.show_dossier_placeholder()
        
    def setup_dossier_content(self):
        """Setup the main dossier content area"""
        # Dossier title
        dossier_title = ctk.CTkLabel(
            self.dossier_main,
            text="Research Dossier",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        dossier_title.pack(pady=(20, 15), padx=20, anchor="w")
        
        # Scrollable content area
        self.dossier_scroll = ctk.CTkScrollableFrame(
            self.dossier_main,
            fg_color="transparent"
        )
        self.dossier_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Key Facts section
        self.key_facts_frame = self.create_dossier_section("Key Facts:", self.dossier_scroll)
        self.key_facts_content = self.create_content_area(self.key_facts_frame, height=120)
        
        # Context & Background section
        self.context_frame = self.create_dossier_section("Context & Background:", self.dossier_scroll)
        self.context_content = self.create_content_area(self.context_frame, height=150)
        
        # Different Angles section
        self.angles_frame = self.create_dossier_section("Different Angles:", self.dossier_scroll)
        self.angles_content = self.create_content_area(self.angles_frame, height=120)
        
        # Related Topics section
        self.related_frame = self.create_dossier_section("Related Topics:", self.dossier_scroll)
        self.related_content = self.create_content_area(self.related_frame, height=100)
    
    def setup_articles_sidebar(self):
        """Setup the articles referenced sidebar"""
        # Sidebar title
        articles_title = ctk.CTkLabel(
            self.articles_sidebar,
            text="Articles Referenced",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        articles_title.pack(pady=(20, 15), padx=15, anchor="w")
        
        # Scrollable articles list
        self.articles_scroll = ctk.CTkScrollableFrame(
            self.articles_sidebar,
            fg_color="transparent"
        )
        self.articles_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 20))
        
    def create_dossier_section(self, title, parent):
        """Create a section frame with title for the dossier"""
        section_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        section_frame.pack(fill="x", pady=(0, 20))
        
        # Section title
        title_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        title_label.pack(fill="x", pady=(0, 8))
        
        return section_frame
    
    def create_content_area(self, parent, height=100):
        """Create a content text area for dossier sections"""
        content_box = ctk.CTkTextbox(
            parent,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            corner_radius=8,
            height=height,
            wrap="word",
            border_width=1,
            border_color=self.colors["border_light"]
        )
        content_box.pack(fill="x")
        content_box.configure(state="disabled")
        return content_box
    
    def show_dossier_placeholder(self):
        """Show placeholder message when no research data is available"""
        placeholder_text = "No script has been generated yet.\n\nGenerate a video script in the Script Generation tab to see research data here."
        
        # Update all content areas with placeholder
        for content_area in [self.key_facts_content, self.context_content, 
                           self.angles_content, self.related_content]:
            content_area.configure(state="normal")
            content_area.delete("0.0", "end")
            content_area.insert("0.0", placeholder_text)
            content_area.configure(state="disabled")
    
    def update_dossier_content(self, research_data):
        """Update dossier with research data from script generation"""
        # Update Key Facts
        self.key_facts_content.configure(state="normal")
        self.key_facts_content.delete("0.0", "end")
        key_facts = research_data.get("key_facts", ["No key facts available"])
        facts_text = "\n".join([f"• {fact}" for fact in key_facts])
        self.key_facts_content.insert("0.0", facts_text)
        self.key_facts_content.configure(state="disabled")
        
        # Update Context & Background
        self.context_content.configure(state="normal")
        self.context_content.delete("0.0", "end")
        context = research_data.get("context", "No context information available")
        self.context_content.insert("0.0", context)
        self.context_content.configure(state="disabled")
        
        # Update Different Angles
        self.angles_content.configure(state="normal")
        self.angles_content.delete("0.0", "end")
        angles = research_data.get("angles", ["No angles available"])
        angles_text = "\n".join([f"• {angle}" for angle in angles])
        self.angles_content.insert("0.0", angles_text)
        self.angles_content.configure(state="disabled")
        
        # Update Related Topics
        self.related_content.configure(state="normal")
        self.related_content.delete("0.0", "end")
        topics = research_data.get("related_topics", ["No related topics available"])
        topics_text = "\n".join([f"• {topic}" for topic in topics])
        self.related_content.insert("0.0", topics_text)
        self.related_content.configure(state="disabled")
        
        # Update articles sidebar
        self.update_articles_sidebar(research_data.get("articles", []))
    
    def update_articles_sidebar(self, articles):
        """Update the articles referenced sidebar"""
        # Clear existing articles
        for widget in self.articles_scroll.winfo_children():
            widget.destroy()
        
        if not articles:
            no_articles_label = ctk.CTkLabel(
                self.articles_scroll,
                text="No articles referenced",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_secondary"]
            )
            no_articles_label.pack(pady=10)
            return
        
        # Add article links
        for i, article in enumerate(articles, 1):
            article_frame = ctk.CTkFrame(
                self.articles_scroll,
                fg_color="transparent"
            )
            article_frame.pack(fill="x", pady=(0, 8))
            
            # Article title (clickable if URL provided)
            if isinstance(article, dict):
                title = article.get("title", f"Article {i}")
                url = article.get("url", "")
            else:
                title = str(article)
                url = ""
            
            article_label = ctk.CTkLabel(
                article_frame,
                text=f"• {title}",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_primary"],
                anchor="w",
                justify="left"
            )
            article_label.pack(fill="x")
            
            if url:
                url_label = ctk.CTkLabel(
                    article_frame,
                    text=f"  {url[:40]}{'...' if len(url) > 40 else ''}",
                    font=ctk.CTkFont(size=10),
                    text_color=self.colors["accent_teal"],
                    anchor="w",
                    justify="left"
                )
                url_label.pack(fill="x")

    def setup_marketing_tools_tab(self):
        """Setup the marketing tools tab"""
        tab_frame = ctk.CTkFrame(
            self.tab3,
            fg_color=self.colors["bg_secondary"],
            corner_radius=15
        )
        tab_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        
        # Topic Analysis Section
        analysis_frame = ctk.CTkFrame(
            tab_frame,
            fg_color=self.colors["bg_card"],
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border_light"]
        )
        analysis_frame.pack(fill="x", padx=40, pady=(20, 20))
        
        # Input section with label, topic field and button in single row
        input_frame = ctk.CTkFrame(
            analysis_frame,
            fg_color="transparent"
        )
        input_frame.pack(fill="x", padx=30, pady=20)
        
        # Topic Analysis label on the left
        analysis_title = ctk.CTkLabel(
            input_frame,
            text="Topic Analysis",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_primary"],
            width=140
        )
        analysis_title.pack(side="left", padx=(0, 15))
        
        # Topic input field
        self.topic_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter a topic to analyze (e.g. 'AI automation', 'healthy cooking')",
            font=ctk.CTkFont(size=16),
            height=40,
            corner_radius=20,
            border_width=2,
            border_color=self.colors["border_light"],
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            placeholder_text_color=self.colors["text_secondary"]
        )
        self.topic_entry.pack(side="left", fill="x", expand=True, padx=(0, 15))
        
        # Analysis button
        self.analyze_button = ctk.CTkButton(
            input_frame,
            text="Get Topic Analysis",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.colors["accent_teal"],
            hover_color=self.colors["accent_teal_hover"],
            corner_radius=20,
            height=40,
            width=160,
            command=self.on_analyze_topic
        )
        self.analyze_button.pack(side="right")
        
        # Two-column layout frame
        columns_frame = ctk.CTkFrame(
            tab_frame,
            fg_color="transparent"
        )
        columns_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        # Left column - Content Gap Analysis (main content area)
        left_column = ctk.CTkFrame(
            columns_frame,
            fg_color="transparent"
        )
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Left column title
        left_title = ctk.CTkLabel(
            left_column,
            text="Content Gap Analysis",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        left_title.pack(pady=(0, 15), anchor="w")
        
        # Content analysis cards container (scrollable)
        self.content_cards_frame = ctk.CTkScrollableFrame(
            left_column,
            fg_color="transparent",
            corner_radius=0
        )
        self.content_cards_frame.pack(fill="both", expand=True)
        
        # Initialize empty content cards
        self.content_cards = {}
        
        # Right column - Sidebar with Title Patterns and Topics
        right_column = ctk.CTkFrame(
            columns_frame,
            fg_color="transparent",
            width=280
        )
        right_column.pack(side="right", fill="y", padx=(10, 0))
        right_column.pack_propagate(False)
        
        # Title Patterns section
        self.patterns_frame = ctk.CTkFrame(
            right_column,
            fg_color=self.colors["bg_card"],
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border_light"]
        )
        self.patterns_frame.pack(fill="x", pady=(0, 15))
        
        patterns_title = ctk.CTkLabel(
            self.patterns_frame,
            text="Title Patterns",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        patterns_title.pack(pady=(15, 5))
        
        self.patterns_textbox = ctk.CTkTextbox(
            self.patterns_frame,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            corner_radius=10,
            wrap="word",
            height=150
        )
        self.patterns_textbox.pack(fill="x", padx=15, pady=(0, 15))
        self.patterns_textbox.insert("0.0", "Title patterns will appear here...")
        self.patterns_textbox.configure(state="disabled")
        
        # Topics Covered section
        self.topics_frame = ctk.CTkFrame(
            right_column,
            fg_color=self.colors["bg_card"],
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border_light"]
        )
        self.topics_frame.pack(fill="x")
        
        topics_title = ctk.CTkLabel(
            self.topics_frame,
            text="Topics Covered",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        topics_title.pack(pady=(15, 5))
        
        self.topics_textbox = ctk.CTkTextbox(
            self.topics_frame,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            corner_radius=10,
            wrap="word",
            height=150
        )
        self.topics_textbox.pack(fill="x", padx=15, pady=(0, 15))
        self.topics_textbox.insert("0.0", "Topics analysis will appear here...")
        self.topics_textbox.configure(state="disabled")
        
        # Timer and status section at bottom
        self.status_frame = ctk.CTkFrame(
            tab_frame,
            fg_color="transparent"
        )
        self.status_frame.pack(fill="x", padx=40, pady=(0, 10))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"]
        )
        self.status_label.pack(side="left")
        
        self.timer_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"]
        )
        self.timer_label.pack(side="right")
        
        # Initialize timer variables
        self.analysis_start_time = None
        self.timer_running = False
    
    def generate_script(self):
        """Handle script generation button click"""
        # Check API key first
        if not self.check_api_key():
            return
            
        # Validate inputs
        topic = self.topic_input.get().strip()
        if not topic:
            messagebox.showerror("Error", "Please enter a main topic")
            return
        
        brand_name = self.brand_input.get().strip()
        if not brand_name:
            messagebox.showerror("Error", "Please enter a brand name")
            return
        
        focus = self.focus_input.get().strip()
        if not focus:
            messagebox.showerror("Error", "Please enter what your brand focuses on")
            return
        
        keypoints_text = self.keypoints_input.get("0.0", "end").strip()
        if not keypoints_text:
            messagebox.showerror("Error", "Please enter key points")
            return
        
        # Parse key points from text
        key_points = []
        for line in keypoints_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*')):
                key_points.append(line.lstrip('-* ').strip())
            elif line and not line.startswith('#'):
                key_points.append(line.strip())
        
        if not key_points:
            messagebox.showerror("Error", "Please enter key points using bullet points (- or *)")
            return
        
        # Get other parameters
        tone = self.tone_input.get()
        try:
            runtime = int(self.runtime_input.get().strip() or "5")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for runtime")
            return
        
        # Disable generate button and show progress
        self.generate_button.configure(state="disabled", text="Generating Script...")
        self.preview_text.configure(state="normal")
        self.preview_text.delete("0.0", "end")
        self.preview_text.insert("0.0", "Generating script... This may take a few minutes.")
        self.preview_text.configure(state="disabled")
        
        # Show preview frame
        self.preview_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Run generation in background thread
        generation_thread = threading.Thread(
            target=self._run_script_generation,
            args=(brand_name, focus, topic, key_points, tone, runtime),
            daemon=True
        )
        generation_thread.start()
    
    def _run_script_generation(self, brand_name, focus, topic, key_points, tone, runtime):
        """Run script generation in background thread"""
        try:
            # Generate script using the script_generator module
            script_content, research_data = generate_script_with_llm(
                brand_name=brand_name,
                we_focus_on=focus,
                main_topic=topic,
                key_points=key_points,
                tone=tone,
                target_runtime=runtime
            )
            
            # Update UI on main thread
            self.root.after(0, self._on_script_generated, script_content, research_data)
            
        except Exception as e:
            error_msg = f"Failed to generate script: {str(e)}"
            self.root.after(0, self._on_script_error, error_msg)
    
    def _on_script_generated(self, script_content, research_data):
        """Handle successful script generation"""
        self.script_content = script_content
        
        # Update preview
        self.preview_text.configure(state="normal")
        self.preview_text.delete("0.0", "end")
        self.preview_text.insert("0.0", script_content)
        self.preview_text.configure(state="disabled")
        
        # Update research dossier with new data
        self.update_dossier_content(research_data)
        
        # Reset button
        self.generate_button.configure(state="normal", text="Generate Script Draft")
    
    def _on_script_error(self, error_msg):
        """Handle script generation error"""
        # Show error in preview
        self.preview_text.configure(state="normal")
        self.preview_text.delete("0.0", "end")
        self.preview_text.insert("0.0", f"Error generating script:\n\n{error_msg}\n\nPlease check:\n- Your API keys are configured\n- Internet connection\n- All required dependencies are installed")
        self.preview_text.configure(state="disabled")
        
        # Reset button
        self.generate_button.configure(state="normal", text="Generate Script Draft")
        
        # Show error dialog
        messagebox.showerror("Generation Error", error_msg)
    
    def save_script(self):
        """Save script as markdown file"""
        if not hasattr(self, 'script_content') or not self.script_content:
            messagebox.showwarning("No Script", "Please generate a script first")
            return
        
        # Get topic for default filename
        topic = self.topic_input.get().strip() or "script"
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
        default_filename = f"script_{safe_topic.lower().replace(' ', '_')}.md"
        
        # Open save dialog
        file_path = filedialog.asksaveasfilename(
            title="Save Script as Markdown",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.script_content)
                messagebox.showinfo("Saved", f"Script saved successfully to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save script:\n{str(e)}")
    
    def copy_script(self):
        """Copy script to clipboard as plain text"""
        if not hasattr(self, 'script_content') or not self.script_content:
            messagebox.showwarning("No Script", "Please generate a script first")
            return
        
        try:
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(self.script_content)
            self.root.update()  # Ensure clipboard is updated
            messagebox.showinfo("Copied", "Script copied to clipboard successfully!")
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy script:\n{str(e)}")
    
    def setup_api_settings_tab(self):
        """Setup the API settings tab"""
        tab_frame = ctk.CTkFrame(
            self.tab4,
            fg_color=self.colors["bg_secondary"],
            corner_radius=15
        )
        tab_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Main container
        main_container = ctk.CTkFrame(
            tab_frame,
            fg_color="transparent"
        )
        main_container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Title
        title_label = ctk.CTkLabel(
            main_container,
            text="API Settings",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title_label.pack(pady=(0, 30))
        
        # API Key section
        api_frame = ctk.CTkFrame(
            main_container,
            fg_color=self.colors["bg_card"],
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border_light"]
        )
        api_frame.pack(fill="x", pady=(0, 20))
        
        # API Key label
        api_label = ctk.CTkLabel(
            api_frame,
            text="OpenRouter API Key:",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        api_label.pack(fill="x", padx=20, pady=(20, 5))
        
        # API Key input
        self.api_key_input = ctk.CTkEntry(
            api_frame,
            placeholder_text="Enter your OpenRouter API key",
            font=ctk.CTkFont(size=14),
            height=35,
            corner_radius=10,
            border_color=self.colors["border_light"],
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            show="*"
        )
        self.api_key_input.pack(fill="x", padx=20, pady=(0, 15))
        
        # Save button
        self.save_api_button = ctk.CTkButton(
            api_frame,
            text="Save API Key",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.colors["accent_teal"],
            hover_color=self.colors["accent_teal_hover"],
            corner_radius=20,
            height=40,
            width=150,
            command=self.save_api_key
        )
        self.save_api_button.pack(pady=(0, 20))
        
        # Status label
        self.api_status_label = ctk.CTkLabel(
            api_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"]
        )
        self.api_status_label.pack(pady=(0, 15))
        
        # Load existing API key
        self.load_api_key()
        
    def setup_analytics_tab(self):
        """Setup the analytics tab"""
        tab_frame = ctk.CTkFrame(
            self.tab5,
            fg_color=self.colors["bg_secondary"],
            corner_radius=15
        )
        tab_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        placeholder_label = ctk.CTkLabel(
            tab_frame,
            text="This is just a tech demo",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        placeholder_label.pack(pady=50)
        
        description_label = ctk.CTkLabel(
            tab_frame,
            text="This demo was created to showcase what is possible when automating with efficiency in mind.",
            font=ctk.CTkFont(size=15),
            text_color=self.colors["text_secondary"],
            justify="center"
        )
        description_label.pack(pady=20)

        description_label_b = ctk.CTkLabel(
            tab_frame,
            text="No fancy and overpriced subscriptions, just the right tools, api calls when necessary, and getting value out of our own hardware.",
            font=ctk.CTkFont(size=15),
            text_color=self.colors["text_secondary"],
            justify="center"
        )
        description_label_b.pack(pady=20)
    
    def save_api_key(self):
        """Save the API key to config file"""
        api_key = self.api_key_input.get().strip()
        if not api_key:
            self.api_status_label.configure(
                text="Please enter an API key",
                text_color=self.colors["error"]
            )
            return
        
        try:
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
            
            config_data["openrouter_api_key"] = api_key
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.api_key = api_key
            os.environ["OPENROUTER_API_KEY"] = api_key
            
            self.api_status_label.configure(
                text="API key saved successfully",
                text_color=self.colors["success"]
            )
            
        except Exception as e:
            self.api_status_label.configure(
                text=f"Failed to save API key: {str(e)}",
                text_color=self.colors["error"]
            )
    
    def load_api_key(self):
        """Load the API key from config file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                api_key = config_data.get("openrouter_api_key", "")
                if api_key:
                    self.api_key = api_key
                    os.environ["OPENROUTER_API_KEY"] = api_key
                    self.api_key_input.insert(0, api_key)
                    self.api_status_label.configure(
                        text="API key loaded",
                        text_color=self.colors["success"]
                    )
                else:
                    self.api_status_label.configure(
                        text="No API key found - please add one",
                        text_color=self.colors["warning"]
                    )
            else:
                self.api_status_label.configure(
                    text="No API key found - please add one",
                    text_color=self.colors["warning"]
                )
                
        except Exception as e:
            self.api_status_label.configure(
                text=f"Error loading config: {str(e)}",
                text_color=self.colors["error"]
            )
    
    def get_api_key(self):
        """Get the current API key"""
        return self.api_key or os.environ.get("OPENROUTER_API_KEY")
    
    def check_api_key(self):
        """Check if API key is available"""
        api_key = self.get_api_key()
        if not api_key:
            messagebox.showerror(
                "API Key Required",
                "Please set your OpenRouter API key in the API Settings tab before using this feature."
            )
            return False
        return True
    
    def on_analyze_topic(self):
        """Handle topic analysis button click"""
        # Check API key first
        if not self.check_api_key():
            return
            
        topic = self.topic_entry.get().strip()
        if not topic:
            self.update_status("Please enter a topic to analyze", is_error=True)
            return
        
        # Disable button and start analysis
        self.analyze_button.configure(state="disabled", text="Analyzing...")
        self.start_timer()
        
        # Clear previous results in all columns
        self.clear_all_columns()
        self.update_column_text(self.patterns_textbox, "Searching videos...")
        self.update_column_text(self.topics_textbox, "Preparing analysis...")  
        self.update_content_cards("Loading analysis...")
        
        # Run analysis in background thread
        analysis_thread = threading.Thread(
            target=self.run_analysis,
            args=(topic,),
            daemon=True
        )
        analysis_thread.start()
    
    def run_analysis(self, topic):
        """Run the analysis in a background thread"""
        try:
            self.update_status("Searching YouTube videos...")
            
            # Step 1: Search for videos
            videos = search_youtube_videos(topic, max_results=8)
            
            if not videos:
                error_msg = "Failed to fetch videos"
                self.root.after(0, self.on_analysis_error, error_msg)
                return
            
            # Step 2: Run individual analyses
            self.root.after(0, lambda: self.update_column_text(self.patterns_textbox, "Analyzing title patterns..."))
            patterns = extract_title_patterns(videos)
            
            self.root.after(0, lambda: self.update_column_text(self.topics_textbox, "Identifying topics..."))
            topics = analyze_video_topics(videos)
            
            self.root.after(0, lambda: self.update_content_cards("Analyzing content gaps..."))
            content_analysis = analyze_video_content_with_llm(videos)
            
            # Update UI on main thread with results
            self.root.after(0, self.on_analysis_complete_columns, patterns, topics, content_analysis, topic)
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            self.root.after(0, self.on_analysis_error, error_msg)
    
    def on_analysis_complete_columns(self, patterns, topics, content_analysis, topic):
        """Handle successful analysis completion for column layout"""
        self.stop_timer()
        
        # Update patterns column
        if patterns and not any("error" in str(p).lower() or "failed" in str(p).lower() for p in patterns):
            patterns_text = "\n".join([f"• {pattern.strip('•-* ')}" for pattern in patterns])
        else:
            patterns_text = "Pattern analysis unavailable\n(API key may not be configured)"
        self.update_column_text(self.patterns_textbox, patterns_text)
        
        # Update topics column
        if topics and not any("error" in str(t).lower() or "failed" in str(t).lower() for t in topics):
            topics_text = "\n".join([f"• {topic.strip('•-* ')}" for topic in topics])
        else:
            topics_text = "Topic analysis unavailable\n(API key may not be configured)"
        self.update_column_text(self.topics_textbox, topics_text)
        
        # Update content analysis with card-based layout
        if content_analysis and not ("error" in content_analysis.lower() or "failed" in content_analysis.lower()):
            self.update_content_cards(content_analysis)
        else:
            self.update_content_cards("Content analysis unavailable\n(API key may not be configured)")
        
        # Reset button
        self.analyze_button.configure(state="normal", text="Get Topic Analysis")
        
        # Update status
        self.update_status(f"Analysis complete for '{topic}'")
    
    def on_analysis_error(self, error_msg):
        """Handle analysis error"""
        self.stop_timer()
        
        # Show error in all columns
        error_text = f"ERROR: {error_msg}\n\nPlease check:\n- Internet connection\n- yt-dlp installation\n- OPENROUTER_API_KEY configuration"
        
        self.update_column_text(self.patterns_textbox, error_text)
        self.update_column_text(self.topics_textbox, error_text)
        self.update_content_cards(error_text)
        
        # Reset button
        self.analyze_button.configure(state="normal", text="Get Topic Analysis")
        self.update_status("Analysis failed", is_error=True)
    
    def clear_all_columns(self):
        """Clear all column textboxes and content cards"""
        # Clear sidebar textboxes
        for textbox in [self.patterns_textbox, self.topics_textbox]:
            textbox.configure(state="normal")
            textbox.delete("0.0", "end")
            textbox.configure(state="disabled")
        
        # Clear content cards
        self.clear_content_cards()
    
    def update_column_text(self, textbox, text):
        """Update text in a specific column textbox"""
        textbox.configure(state="normal")
        textbox.delete("0.0", "end")
        textbox.insert("0.0", text)
        textbox.configure(state="disabled")
    
    def format_markdown_for_display(self, text):
        """Convert markdown to human-readable text"""
        if not text or text.strip() in ["Loading...", "Content analysis will appear here..."]:
            return text
            
        # Remove markdown formatting and make text more readable
        formatted = text
        
        # Convert headers to plain text with spacing
        formatted = re.sub(r'^#{1,6}\s*(.+)$', r'\1\n' + '='*40, formatted, flags=re.MULTILINE)
        
        # Convert bold text
        formatted = re.sub(r'\*\*(.+?)\*\*', r'\1', formatted)
        formatted = re.sub(r'__(.+?)__', r'\1', formatted)
        
        # Convert italic text (remove formatting)
        formatted = re.sub(r'\*(.+?)\*', r'\1', formatted)
        formatted = re.sub(r'_(.+?)_', r'\1', formatted)
        
        # Convert bullet points
        formatted = re.sub(r'^\s*[-*+]\s+(.+)$', r'• \1', formatted, flags=re.MULTILINE)
        
        # Convert numbered lists
        formatted = re.sub(r'^\s*\d+\.\s+(.+)$', r'→ \1', formatted, flags=re.MULTILINE)
        
        # Clean up excessive newlines but preserve paragraph breaks
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        
        # Add spacing after sections
        formatted = re.sub(r'(={40})\n', r'\1\n\n', formatted)
        
        return formatted.strip()
    
    def clear_content_cards(self):
        """Clear all content cards from the main content area"""
        for widget in self.content_cards_frame.winfo_children():
            widget.destroy()
        self.content_cards = {}
    
    def update_content_cards(self, content_text):
        """Parse markdown content and create separate cards for each section"""
        self.clear_content_cards()
        
        if not content_text or "unavailable" in content_text.lower() or "error" in content_text.lower():
            # Show error or unavailable message in single card
            self.create_content_card("Status", content_text)
            return
        
        # Parse markdown content into sections
        sections = self.parse_markdown_sections(content_text)
        
        if not sections:
            # Fallback to single card if parsing fails
            self.create_content_card("Analysis Results", content_text)
            return
        
        # Priority order for cards - actionable items first
        priority_keywords = ["actionable", "action", "recommendations", "items", "next steps", "todo"]
        
        # Create priority cards first
        created_sections = set()
        for title, content in sections.items():
            if any(keyword in title.lower() for keyword in priority_keywords):
                if content.strip():
                    formatted_content = self.format_card_content(content)
                    self.create_content_card(title, formatted_content)
                    created_sections.add(title)
        
        # Create remaining cards
        for title, content in sections.items():
            if title not in created_sections and content.strip():
                formatted_content = self.format_card_content(content)
                self.create_content_card(title, formatted_content)
    
    def parse_content_sections(self, content_text):
        """Parse content text into sections based on headers"""
        sections = {}
        current_section = None
        current_content = []
        
        lines = content_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_content:
                    current_content.append('')
                continue
                
            # Check if this is a header (starts with #, **text**, or is all caps)
            is_header = (
                line.startswith('#') or
                (line.startswith('**') and line.endswith('**')) or
                (line.isupper() and len(line.split()) <= 4 and not line.startswith('•'))
            )
            
            if is_header:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section - clean up asterisks, numbers, and formatting
                clean_title = line.strip('#* ').replace('*', '').strip()
                # Remove leading numbers and periods (e.g., "1. Title" -> "Title")
                clean_title = re.sub(r'^\d+\.\s*', '', clean_title)
                current_section = clean_title.title()
                current_content = []
            else:
                # Add to current section
                if current_section:
                    current_content.append(line)
                else:
                    # No header found yet, create default section
                    if not current_section:
                        current_section = "Analysis Results"
                        current_content = [line]
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def parse_markdown_sections(self, content_text):
        """Parse markdown content into sections based on headers"""
        sections = {}
        current_section = None
        current_content = []
        
        lines = content_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_content:
                    current_content.append('')
                continue
            
            # Check if this is a markdown header
            if line.startswith('#') or (line.startswith('**') and line.endswith('**')):
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section - clean up formatting and numbers
                if line.startswith('#'):
                    clean_title = line.lstrip('# ').strip()
                else:
                    clean_title = line.strip('*').strip()
                
                # Remove leading numbers (e.g., "1. Common Themes" -> "Common Themes")
                clean_title = re.sub(r'^\d+\.\s*', '', clean_title)
                # Remove other numbering patterns
                clean_title = re.sub(r'^\d+\)\s*', '', clean_title)
                clean_title = re.sub(r'^\d+\s*[-–]\s*', '', clean_title)
                
                current_section = clean_title.strip()
                current_content = []
            else:
                # Add to current section
                if current_section:
                    current_content.append(line)
                else:
                    # No header found yet, create default section
                    if not current_section:
                        current_section = "Overview"
                        current_content = [line]
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def format_card_content(self, content):
        """Format content for display in cards"""
        if not content:
            return content
        
        # Clean up markdown formatting for better readability
        formatted = content
        
        # Convert markdown bold to plain text (keep emphasis through context)
        formatted = re.sub(r'\*\*(.+?)\*\*', r'\1', formatted)
        formatted = re.sub(r'__(.+?)__', r'\1', formatted)
        
        # Convert markdown italic to plain text
        formatted = re.sub(r'\*(.+?)\*', r'\1', formatted)
        formatted = re.sub(r'_(.+?)_', r'\1', formatted)
        
        # Improve bullet points
        formatted = re.sub(r'^[\s]*[-*+]\s+', '• ', formatted, flags=re.MULTILINE)
        
        # Improve numbered lists
        formatted = re.sub(r'^\s*\d+\.\s+', '→ ', formatted, flags=re.MULTILINE)
        
        # Clean up excessive whitespace
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        
        # Remove leading/trailing whitespace
        formatted = formatted.strip()
        
        return formatted
    
    def extract_actionable_recommendations(self, content_text):
        """Extract actionable recommendations from content text"""
        lines = content_text.split('\n')
        recommendations = []
        in_recommendations_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if we're entering a recommendations section
            if any(keyword in line.lower() for keyword in ['actionable recommendations', 'recommendations', 'action items']):
                if line.startswith('#') or line.startswith('**') or line.isupper():
                    in_recommendations_section = True
                    continue
            
            # Check if we're leaving the recommendations section (new header)
            elif in_recommendations_section and (line.startswith('#') or 
                                               (line.startswith('**') and line.endswith('**')) or
                                               (line.isupper() and len(line.split()) <= 4 and not line.startswith('•'))):
                break
            
            # Collect recommendation content
            elif in_recommendations_section:
                recommendations.append(line)
        
        return '\n'.join(recommendations).strip() if recommendations else None
    
    def create_content_card(self, title, content):
        """Create a single content card with title and content"""
        card_frame = ctk.CTkFrame(
            self.content_cards_frame,
            fg_color=self.colors["bg_card"],
            corner_radius=15,
            border_width=1,
            border_color=self.colors["border_light"]
        )
        card_frame.pack(fill="x", pady=(0, 15))
        
        # Card title
        title_label = ctk.CTkLabel(
            card_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        title_label.pack(fill="x", padx=15, pady=(15, 5))
        
        # Card content
        content_textbox = ctk.CTkTextbox(
            card_frame,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_card"],
            text_color=self.colors["text_primary"],
            corner_radius=10,
            wrap="word",
            height=min(200, max(80, len(content.split('\n')) * 20))
        )
        content_textbox.pack(fill="x", padx=15, pady=(0, 15))
        
        # Insert the already formatted content
        content_textbox.insert("0.0", content)
        content_textbox.configure(state="disabled")
        
        # Store reference
        self.content_cards[title] = content_textbox
        
        return card_frame
    
    def start_timer(self):
        """Start the analysis timer"""
        self.analysis_start_time = time.time()
        self.timer_running = True
        self.update_timer()
    
    def stop_timer(self):
        """Stop the analysis timer"""
        self.timer_running = False
        if self.analysis_start_time:
            elapsed_time = time.time() - self.analysis_start_time
            self.timer_label.configure(text=f"Completed in {elapsed_time:.1f}s")
    
    def update_timer(self):
        """Update the timer display"""
        if self.timer_running and self.analysis_start_time:
            elapsed_time = time.time() - self.analysis_start_time
            self.timer_label.configure(text=f"Running: {elapsed_time:.1f}s")
            # Schedule next update
            self.root.after(100, self.update_timer)
    
    
    def update_status(self, message, is_error=False):
        """Update the status label"""
        color = self.colors["error"] if is_error else self.colors["text_secondary"]
        self.status_label.configure(text=message, text_color=color)
    
    def run(self):
        """Start the application"""
        logger.info("Starting AI Script Generator application...")
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        app = AIScriptGeneratorApp()
        app.run()
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()