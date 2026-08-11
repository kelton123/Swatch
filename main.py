'''
The main UI for colour clipboard using tkinter as the graphical layer.
'''

import json
import mss
import os
import time
import sys

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import _tkinter # For tkinter errors

from PIL import ImageTk, Image, ImageCms

import widgets as widgets
import colours as cl


'''
CONSTANTS
'''
WINDOW_PADDING = 40

def clamp(x): 
  return max(0, min(x, 255))

def rgb_to_hex(r,g,b,a=None):
    return "{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for py2app bundle."""
    # os.path.abspath(__file__) points inside Contents/Resources/ when running in py2app
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class ColourCoperUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Swatch")
        self.root.geometry("854x480")
        self.root.minsize(854,480)
        self.root.config(background = cl.CC_WHITE)
        self.root.resizable(False, False)

        self.root.bind('<<NotebookTabChanged>>', lambda event: self.root.update_idletasks())

        self.centre_launch(self.root, 854, 480)

        # Tracks every open project tab, keyed by its content frame (the
        # widget the Notebook uses as the tab's identifier): frame ->
        # {name, add_button, filepath, dirty}. Each tab is its own
        # "document", saved/loaded independently (like tabs in Illustrator).
        # The Notebook widget itself is the single source of truth for
        # which tab is active and how tabs are displayed/switched.
        self.tabs = {}

        # Load images that can be used later
        dropper_icon = Image.open(get_resource_path("icons/dropper.png"))
        dropper_icon = dropper_icon.resize((18,18))
        self.eyedrop_icon = ImageTk.PhotoImage(dropper_icon)

        '''
        LAYOUT
        '''
        # Header section with project name, save and import buttons.
        self.header_frame = tk.Frame(root, height = 100, bg = cl.CC_WHITE)
        self.header_frame.pack(side = "top", fill = "x", padx = WINDOW_PADDING, pady=(WINDOW_PADDING / 2))

        # Tab + swatches section: the Notebook shows the tab strip and the
        # active tab's swatch cards together, so this frame needs to expand
        # to fill the remaining vertical space (previously split between a
        # separate tab_frame and swatches_frame).
        self.tab_frame = tk.Frame(root, bg = cl.CC_WHITE)
        self.tab_frame.pack(side = "top", fill = "both", expand = True, padx = WINDOW_PADDING, pady = (0, 20))


        # Footer section
        self.footer_frame = tk.Frame(root, height = 50, bg = cl.CC_WHITE)
        self.footer_frame.pack(side = "bottom", fill = "x", padx = WINDOW_PADDING)


        '''
        HEADER SECTION
        
        |[project name]                 [save][load]|
        '''
        # Configure column 1 and 5 to expand and create white space.
        self.header_frame.columnconfigure(3, weight=2)

        # SWATCH TOOLS
        # Tint adjustment
        self.tint_entry = tk.Entry(
            self.header_frame,
            highlightbackground=cl.CC_WHITE,
            bg=cl.CC_PURE_WHITE,
            fg=cl.CC_BLACK,
            font=("futura-book", 12),
            width=5
            )

        # Pre-fill with percentage as a helper
        self.tint_entry.insert(0, "100%")
        self.tint_entry.grid(row=0, column=0, padx=(0, 4))

        # Update all of the swatches when the widget is unfocused.
        self.tint_entry.bind("<FocusOut>", self.update_swatch_tint)

        # Add the hover label class
        widgets.CursorFollowerLabel(
            self.tint_entry,
            text=f"Tint + Shade Adjustment\n\nUpdate the percentage to add more white (0-100)\nor more black (-95-0) to all swatches.\nPress Enter to confirm.")

        # Colour code format dropdown
        # Dropdown options  
        self.colour_codes = ["hex", "rgb", "cmyk", "hsl"]

        self.format_combobox = ttk.Combobox(
            self.header_frame,
            values=self.colour_codes,
            width=5,
            state="readonly",
            font=("futura-book", 12)
            )
        self.format_combobox.set("hex")
        self.format_combobox.grid(row=0, column=1, padx=(4,0))
        self.format_combobox.bind("<<ComboboxSelected>>", self.update_all_swatches_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.format_combobox, text=f"Colour Format | ⌘ + F\n\nUse the dropdown to update the\ncolour code on all swatches.")

        # NEW SWATCH BUTTON
        new_swatch_icon = Image.open(get_resource_path("icons/plus.png"))
        new_swatch_icon = new_swatch_icon.resize((18,18))
        self.new_swatch_image = ImageTk.PhotoImage(new_swatch_icon)

        self.new_swatch_border = tk.Frame(
            self.header_frame,
            bg=cl.CC_LIGHT_GREY,
            padx=1,
            pady=1
        )
        self.new_swatch_border.grid(row=0, column=4, padx=4)

        self.new_swatch_button = tk.Label(
            self.new_swatch_border,
            text=" Swatch",
            image=self.new_swatch_image,
            highlightbackground=cl.CC_WHITE,
            bg=cl.CC_PURE_WHITE,
            fg=cl.CC_BLACK,
            compound="left",
            font=("futura", 12)
            )
        self.new_swatch_button.pack(ipadx=4, ipady=4)

        # Bind the new swatch button
        self.new_swatch_button.bind("<Button-1>", lambda event: self.add_new_swatch())
        self.new_swatch_button.bind("<Enter>", self.on_hover_label)
        self.new_swatch_button.bind("<Leave>", self.on_leave_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.new_swatch_button, text="New Swatch | ⌘ + N")

        # NEW PROJECT BUTTON
        new_folder_icon = Image.open(get_resource_path("icons/folder-plus.png"))
        new_folder_icon = new_folder_icon.resize((18,18))
        self.new_project_image = ImageTk.PhotoImage(new_folder_icon)

        self.new_project_border = tk.Frame(
            self.header_frame,
            bg=cl.CC_LIGHT_GREY,
            padx=1,
            pady=1
        )
        self.new_project_border.grid(row=0, column=5, padx=4)

        self.add_notebook = tk.Label(
            self.new_project_border,
            image=self.new_project_image,
            bg=cl.CC_PURE_WHITE,
            fg=cl.CC_BLACK,
            )
        self.add_notebook.pack(ipadx=4, ipady=4)

        # Bind the new project button
        self.add_notebook.bind("<Button-1>", lambda event: self.add_new_project_tab())
        self.add_notebook.bind("<Enter>", self.on_hover_label)
        self.add_notebook.bind("<Leave>", self.on_leave_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.add_notebook, text="New Project | ⌘ + P")

        # SAVE PROJECT BUTTON
        save_icon = Image.open(get_resource_path("icons/save-01.png"))
        save_icon = save_icon.resize((18,18))
        self.save_image = ImageTk.PhotoImage(save_icon)

        self.save_border = tk.Frame(
            self.header_frame,
            bg=cl.CC_LIGHT_GREY,
            padx=1,
            pady=1
        )
        self.save_border.grid(row=0, column=7, padx=4)

        self.save_button = tk.Label(
            self.save_border,
            image=self.save_image,
            bg=cl.CC_PURE_WHITE,
            padx=5,
            pady=5,
            )
        self.save_button.pack(ipadx=4, ipady=4)

        # Bind the save button
        self.save_button.bind("<Button-1>", lambda event: self.save_active_tab())
        self.save_button.bind("<Enter>", self.on_hover_label)
        self.save_button.bind("<Leave>", self.on_leave_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.save_button, text="Save Project | ⌘ + S")

        # OPEN PROJECT BUTTON
        load_icon = Image.open(get_resource_path("icons/folder-open.png"))
        load_icon = load_icon.resize((20,20))
        self.load_image = ImageTk.PhotoImage(load_icon)

        self.load_border = tk.Frame(
            self.header_frame,
            bg=cl.CC_LIGHT_GREY,
            padx=1,
            pady=1
        )
        self.load_border.grid(row = 0, column = 8, padx=4)

        self.load_button = tk.Label(
            self.load_border,
            image=self.load_image,
            bg=cl.CC_PURE_WHITE,
            padx=3,
            pady=3
            )
        self.load_button.pack(ipadx=4, ipady=4)

        # Bind the load button
        self.load_button.bind("<Button-1>", lambda event: self.load_project_tab())
        self.load_button.bind("<Enter>", self.on_hover_label)
        self.load_button.bind("<Leave>", self.on_leave_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.load_button, text="Open Project | ⌘ + O")

        # DELETE PROJECT BUTTON
        delete_icon = Image.open(get_resource_path("icons/trash.png"))
        delete_icon = delete_icon.resize((16,16))
        self.delete_image = ImageTk.PhotoImage(delete_icon)

        self.delete_border = tk.Frame(
            self.header_frame,
            bg=cl.CC_LIGHT_GREY,
            padx=1,
            pady=1
        )
        self.delete_border.grid(row = 0, column =9, padx=4)

        self.delete_palette_button = tk.Label(
            self.delete_border, 
            bg=cl.CC_PURE_WHITE,
            image=self.delete_image,
            padx=5,
            pady=5,
            )
        self.delete_palette_button.pack(ipadx=4, ipady=4)

        # Bind delete tab button
        self.delete_palette_button.bind("<Button-1>", lambda event: self._open_delete_tab_popup())
        self.delete_palette_button.bind("<Enter>", self.on_hover_label)
        self.delete_palette_button.bind("<Leave>", self.on_leave_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.delete_palette_button, text="Delete Project | ⌘ + D")

        '''
        TAB SECTION

        |[project tab] [project tab] [+]        |
        '''
        # The Notebook control handles tab buttons, switching, and active
        # styling automatically - we just add/remove/rename its child frames.
        self.notebook = ttk.Notebook(self.tab_frame)
        self.notebook.pack(side = "left", fill = "both", expand = True)


        '''
        FOOTER SECTION
        '''
        footer_text = widgets.LabelFooter(self.footer_frame, text = "Designed & Developed by Kelton Boyter-Grant", bg = cl.CC_WHITE)
        footer_text.pack(padx=20, pady=(0, 20), expand=True)

        '''
        KEYBOARD BINDINGS
        '''
        # Save the active tab swatches
        self.root.bind("<Command-s>", self.save_active_tab)
        self.root.bind("<Command-S>", self.save_active_tab)
        self.root.bind("<Control-s>", self.save_active_tab)
        self.root.bind("<Control-S>", self.save_active_tab)

        # Delete the active tab
        self.root.bind("<Command-d>", self._open_delete_tab_popup)
        self.root.bind("<Command-D>", self._open_delete_tab_popup)
        self.root.bind("<Control-d>", self._open_delete_tab_popup)
        self.root.bind("<Control-D>", self._open_delete_tab_popup)

        # Load a swatch file
        self.root.bind("<Command-o>", self.load_project_tab)
        self.root.bind("<Command-O>", self.load_project_tab)
        self.root.bind("<Control-o>", self.load_project_tab)
        self.root.bind("<Control-O>", self.load_project_tab)

        # Add a new swatch
        self.root.bind("<Command-n>", self.add_new_swatch)
        self.root.bind("<Command-N>", self.add_new_swatch)
        self.root.bind("<Control-n>", self.add_new_swatch)
        self.root.bind("<Control-N>", self.add_new_swatch)

        # Cycle the dropdown box of colour formats
        self.root.bind("<Command-f>", self.cycle_colour_format)
        self.root.bind("<Command-F>", self.cycle_colour_format)
        self.root.bind("<Control-f>", self.cycle_colour_format)
        self.root.bind("<Control-F>", self.cycle_colour_format)

        # Create a new project tab
        self.root.bind("<Command-p>", self.add_new_project_tab)
        self.root.bind("<Command-P>", self.add_new_project_tab)
        self.root.bind("<Control-p>", self.add_new_project_tab)
        self.root.bind("<Control-P>", self.add_new_project_tab)

        self.tint_entry.bind("<Return>", self._focus_main_window)


    '''
    UI FUNCTIONS
    '''
    def _focus_main_window(self, event=None):
        self.root.focus()

    # Launch the window in the centre of the screen.
    def centre_launch(self, window, window_width=960, window_height=540):
        center_x, center_y = self.get_screen_centre()

        # set the position of the window to the center of the screen
        window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    # Get the centre coordinates of the user's screen
    def get_screen_centre(self):
        # get the screen dimension
        screen_width  = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        window_width  = 960
        window_height = 540

        # find the center point
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)

        return center_x, center_y
    
    def on_hover_label(self, event=None):
        if event and event.widget:
            self._set_bg_recursive(event.widget, cl.CC_LIGHT_GREY)

    def on_leave_label(self, event=None):
        if event and event.widget:
            self._set_bg_recursive(event.widget, cl.CC_PURE_WHITE)

    def _set_bg_recursive(self, widget, color):
        widgets_to_update = [widget]
        while widgets_to_update:
            current = widgets_to_update.pop()
            try:
                current.config(bg=color)
            except tk.TclError:
                pass
            widgets_to_update.extend(current.winfo_children())
    
    def cycle_colour_format(self, event=None):
        # Get the current format
        current_format = self.format_combobox.get()

        # Get position in the master list of formats
        current_index = self.colour_codes.index(current_format)

        if current_index == len(self.colour_codes) -1:
            current_index = -1

        new_format = self.colour_codes[current_index + 1]
        
        self.format_combobox.set(new_format)

        # Update the swatch widget labels
        self.update_all_swatches_label()


    # Add a new swatch in the active tab
    def add_new_swatch(self, event=None):
        active_tab_id = self._get_active_tab_id()
        if active_tab_id is None:
            messagebox.showwarning("Warning", "No project tab to add new swatch to!", parent=self.root)
            return
        self.open_swatch_popup(active_tab_id)

    # Create a new swatch inside the given tab
    def open_swatch_popup(self, tab_id, hex=None):
        # Create the top-level pop-up window        
        popup = widgets.create_popup(self.root, "Add Swatch", 260, 225)

        # POPUP LAYOUT
        # Configure layout spacing for the popup
        popup.columnconfigure(1, weight=1)

        # Colour preview
        colour_preview = tk.Frame(
            popup,
            background=cl.CC_BLACK,
            height=75
        )
        colour_preview.grid(row=0, column=0, rowspan=2, columnspan=3, sticky="nesw", pady=(0,5))

        # Name Entry Widget
        lbl_name = tk.Label(popup, text="Name:", bg=cl.CC_WHITE, fg=cl.CC_BLACK, highlightbackground=cl.CC_WHITE, font=("futura-book", 12))
        lbl_name.grid(row=2, column=0, sticky="w", pady=5)
        
        ent_name = tk.Entry(popup, bg=cl.CC_PURE_WHITE, highlightbackground=cl.CC_WHITE, font=("futura-book", 14))
        ent_name.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=5)
        ent_name.focus_set()  # Automatically place cursor in this box

        # Hex Entry Widget
        lbl_hex = tk.Label(popup, text="Hex Code: #", bg=cl.CC_WHITE, fg=cl.CC_BLACK, font=("futura-book", 12), highlightbackground=cl.CC_WHITE)
        lbl_hex.grid(row=3, column=0, sticky="w", pady=5)
        
        self.ent_hex = tk.Entry(popup, bg=cl.CC_PURE_WHITE, highlightbackground=cl.CC_WHITE, font=("futura-book", 14))
        self.ent_hex.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=5)

        # Bind every key press to check if a hex code has been supplied to update the colour preview
        def update_colour_preview(event):
            # Exit early on special characters
            key_name = event.keysym
            special_chars = ["Return", "Delete", "Space", "Left", "Right", "Up", "Down", "Shift", "Lock", "BackSpace"]
            if key_name in special_chars:
                return

            # Format the entry text to always be uppercase
            hex_code = self.ent_hex.get().strip()
            self.ent_hex.delete(0, tk.END)
            self.ent_hex.insert(0, hex_code.upper())

            # Do not update the preview with less than 6 characters (a hex code length.)
            if len(hex_code) != 6:
                return

            # Try to update the preview frame background colour.
            try:
                colour_preview.config(bg=f"#{hex_code}")
            except _tkinter.TclError:
                messagebox.showwarning("Warning", "Please enter a valid hex code, e.g. #FF8D28", parent=popup)
                return
                    
        self.ent_hex.bind("<KeyRelease>", update_colour_preview)

        # Eyedropper button to get a hex code from the screen (by taking a screenshot)
        eyedrop_button_border = tk.Frame(
            popup,
            bg=cl.CC_LIGHT_GREY,
            padx=1,
            pady=1
        )
        eyedrop_button_border.grid(row=3, column=2, padx=4)

        eyedrop_button = tk.Label(
            eyedrop_button_border,
            image=self.eyedrop_icon,
            highlightbackground=cl.CC_WHITE,
            bg=cl.CC_PURE_WHITE,
            )
        eyedrop_button.pack(ipadx=2, ipady=2, side="right")

        def handle_eyedropper_click(event=None):
            hex_code = self.get_eyedropper_hex(parent_popup=popup)
            if hex_code:
                # Update Entry Widget
                self.ent_hex.delete(0, tk.END)
                self.ent_hex.insert(0, hex_code.upper())
                
                # Update Preview Frame
                try:
                    colour_preview.config(bg=f"#{hex_code}")
                except _tkinter.TclError:
                    pass

        # Bind the new swatch button
        eyedrop_button.bind("<Button-1>", handle_eyedropper_click)
        eyedrop_button.bind("<Enter>",    self.on_hover_label)
        eyedrop_button.bind("<Leave>",    self.on_leave_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(eyedrop_button, text=f"Eyedropper\n\nClick a pixel to sample its hex code")

        if hex:
            self.ent_hex.insert(0, hex)

        #  BUTTON FUNCTIONS
        def save_action():
            name_data = ent_name.get().strip().title()
            hex_data  = self.ent_hex.get().strip()

            if hex_data is None and hex is not None:
                hex_data = hex

            # Simple validation check
            if not name_data or not hex_data:
                messagebox.showwarning("Warning", "Both fields are required!", parent=popup)
                return
            
            # Check for name length
            if len(name_data) > 20:
                messagebox.showwarning("Warning", "Name too long. Please keep the name under 20 characters", parent=popup)
                return
                
            # Create a new swatch widget from the user's input values.
            try:
                # Add the leading # to the hex string
                hex_data = f"#{hex_data.upper()}"

                self._add_swatch_to_tab(tab_id, name_data, hex_data)
            except _tkinter.TclError:
                messagebox.showwarning("Warning", "Please enter a valid hex code, e.g. #FF8D28", parent=popup)
                return

            popup.destroy()  # Close the popup window after saving [3]

        def _save_action_shortcut(self):
            save_action()

        def close_popup(self):
            popup.destroy()

        # Buttons Layout Frame (at the bottom)
        btn_frame = tk.Frame(popup, bg=cl.CC_WHITE)
        btn_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(5,0))
        btn_frame.columnconfigure(0, weight=1) # Invisible space pushing buttons right

        # Close Button
        btn_close = tk.Button(
            btn_frame,
            text                = "Close",
            bg                  = cl.CC_WHITE,
            fg                  = cl.CC_BLACK,
            font                = ("futura-book", 12),
            highlightbackground = cl.CC_WHITE,
            command             = popup.destroy
            )
        btn_close.grid(row=0, column=1, padx=5)

        # Save Button
        btn_save = tk.Button(
            btn_frame,
            text                = "Save",
            bg                  = cl.CC_WHITE,
            fg                  = cl.CC_BLACK,
            font                = ("futura-book", 12),
            highlightbackground = cl.CC_WHITE,
            command             = save_action
            )
        btn_save.grid(row=0, column=2, padx=5)

        # Bind keyboard inputs
        popup.bind("<Return>", _save_action_shortcut)
        popup.bind("<Escape>", close_popup)

    # Create a new, empty project tab via a name-entry pop-up
    def add_new_project_tab(self, event=None):
        popup = widgets.create_popup(self.root, "New Project", 320, 110)

        lbl_name = tk.Label(popup, text="Name:", font=("futura-book", 12), bg=cl.CC_WHITE)
        lbl_name.grid(row=0, column=0, sticky="w", pady=(0,15), padx=(0,15))

        ent_name = tk.Entry(popup, font=("futura-book", 14), highlightbackground=cl.CC_WHITE, bg=cl.CC_PURE_WHITE)
        ent_name.grid(row=0, column=1, sticky="w", pady=(0,15))
        ent_name.focus_set()

        def create_action(event=None):
            name = ent_name.get().strip().title()
            if not name:
                messagebox.showwarning("Warning", "Please enter a project name!", parent=popup)
                return
            self._create_tab(name)
            popup.destroy()
        
        def close_popup(self):
            popup.destroy()

        btn_frame = tk.Frame(popup, bg=cl.CC_WHITE)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(15,0))
        btn_frame.columnconfigure(0, weight=1)

        btn_close = tk.Button(btn_frame, text="Cancel", font=("futura-book", 12), bg=cl.CC_WHITE, highlightbackground=cl.CC_WHITE, command=popup.destroy)
        btn_close.grid(row=0, column=1, padx=(0,5))

        btn_create = tk.Button(btn_frame, text="Create", font=("futura-book", 12), bg=cl.CC_WHITE, highlightbackground=cl.CC_WHITE, command=create_action)
        btn_create.grid(row=0, column=2, padx=(5,0))

        # Bind keyboard inputs
        popup.bind("<Escape>", close_popup)
        popup.bind("<Return>", create_action)

    # TINT FUNCTION
    def update_swatch_tint(self, event=None):
        tint_value = self.tint_entry.get().replace("%", "").strip()     

        if tint_value is None:
            return
        
        try:
            tint_value = int(tint_value)
            if tint_value > 100 or tint_value < -95:
                raise ValueError
            
        except ValueError:
            messagebox.showwarning("Warning", "Please enter a valid value between -95 to 100", parent=self.root)
            return

        # Remove focus from the combobox
        self._focus_main_window()

        self.tint_entry.delete(0, "end")
        if tint_value == 0:
            # Setting to 0 will be pure white, reset to the original colour
            self.tint_entry.insert(0, "100%")
            tint_value = 100
        else:
            self.tint_entry.insert(0, f"{tint_value}%")

        for tab_frame, tab_data in list(self.tabs.items()):
            if not tab_frame.winfo_exists():
                continue
            swatches = [w for w in tab_frame.winfo_children() if isinstance(w, widgets.Swatch)]
            if swatches:
                for swatch in swatches:
                    swatch.update_colour_tint(int(tint_value))

# EYEDROPPER FUNCTIONS
    def get_eyedropper_hex(self, parent_popup=None):
        """
        Captures the screen and returns the hex code of the clicked pixel.
        Returns None if the user cancels with Escape.
        """
        # 1. Hide the main app and the swatch popup during capture
        self.root.withdraw()
        if parent_popup:
            parent_popup.withdraw()

        # Give the window manager a moment to actually finish hiding the
        # windows before we grab the screen - a single update() isn't a
        # hard guarantee, especially with animated hide/show (e.g. macOS).
        for _ in range(4):
            self.root.update()
            time.sleep(0.05)

        selected_hex = [None]
        overlay = None

        try:
            # 2. Capture the screen with mss & handle P3 color space conversion
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                raw_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                p3_profile_path = "/System/Library/ColorSync/Profiles/Display P3.icc"
                if os.path.exists(p3_profile_path):
                    try:
                        p3_profile = ImageCms.ImageCmsProfile(p3_profile_path)
                        srgb_profile = ImageCms.createProfile("sRGB")
                        transform = ImageCms.buildTransform(p3_profile, srgb_profile, "RGB", "RGB")
                        screen_img = ImageCms.applyTransform(raw_img, transform)
                    except Exception as e:
                        print(f"Color conversion failed: {e}")
                        screen_img = raw_img
                else:
                    screen_img = raw_img

            # 3. Create Fullscreen Overlay
            overlay = tk.Toplevel(self.root)
            overlay.attributes("-fullscreen", True)
            overlay.attributes("-topmost", True)
            overlay.config(cursor="crosshair")

            # Display image on Canvas
            tk_img = ImageTk.PhotoImage(screen_img)
            screen_width = overlay.winfo_screenwidth()
            screen_height = overlay.winfo_screenheight()

            canvas = tk.Canvas(overlay, highlightthickness=0, width=screen_width, height=screen_height)
            canvas.pack(fill="both", expand=True)
            canvas.create_image(0, 0, image=tk_img, anchor="nw")
            canvas.image = tk_img  # keep a reference so Tk doesn't garbage-collect it

            # 4. Define Event Callbacks
            def on_pixel_click(event):
                scale_factor = screen_img.width / overlay.winfo_screenwidth()
                actual_x = int(event.x * scale_factor)
                actual_y = int(event.y * scale_factor)

                actual_x = max(0, min(actual_x, screen_img.width - 1))
                actual_y = max(0, min(actual_y, screen_img.height - 1))

                r, g, b = screen_img.getpixel((actual_x, actual_y))[:3]
                selected_hex[0] = rgb_to_hex(r, g, b)
                overlay.destroy()

            def on_cancel(event=None):
                overlay.destroy()

            canvas.bind("<Button-1>", on_pixel_click)
            overlay.bind("<Escape>", on_cancel)

            overlay.focus_force()
            overlay.grab_set()

            # 5. Pause execution until the overlay window is closed
            self.root.wait_window(overlay)

        finally:
            # 6. ALWAYS restore hidden windows, even if something above raised
            if overlay is not None and overlay.winfo_exists():
                overlay.destroy()
            if parent_popup:
                parent_popup.deiconify()
            self.root.deiconify()

        # Return the resulting hex string (or None)
        return selected_hex[0]

    '''
    TAB MANAGEMENT
    '''

    # Create a new tab (content frame + "+" swatch button) and switch to it.
    # The frame itself is used as the tab's identifier throughout, since
    # that's what ttk.Notebook expects.
    def _create_tab(self, name):
        # Outer container added to the notebook
        tab_container = tk.Frame(self.notebook)

        # Canvas & Scrollbar setup inside tab_container
        tab_canvas = tk.Canvas(tab_container, bg=cl.CC_WHITE, highlightthickness=0)
        tab_scrollbar = tk.Scrollbar(tab_container, orient="vertical", command=tab_canvas.yview)
        tab_canvas.configure(yscrollcommand=tab_scrollbar.set)

        tab_scrollbar.pack(side="right", fill="y")
        tab_canvas.pack(side="left", fill="both", expand=True)

        # Content frame (where swatch cards will actually be placed)
        tab_frame = tk.Frame(tab_canvas, bg=cl.CC_WHITE)
        canvas_window = tab_canvas.create_window((0, 0), window=tab_frame, anchor="nw")

        # Synchronize scrolling region and width
        def on_frame_configure(event):
            # Update scrollable area whenever child widgets change
            bbox = tab_canvas.bbox("all")
            if bbox:
                tab_canvas.configure(scrollregion=bbox)

        def on_canvas_configure(event):
            # Dynamically resize inner tab_frame to fit canvas width
            tab_canvas.itemconfig(canvas_window, width=event.width)

        tab_frame.bind("<Configure>", on_frame_configure)
        tab_canvas.bind("<Configure>", on_canvas_configure)

        # Enable Mousewheel / Trackpad Scrolling
        def _on_mousewheel(event):
            # Handles macOS trackpad/mousewheel scrolling
            delta = event.delta if event.delta != 0 else -event.num
            tab_canvas.yview_scroll(int(-1 * delta), "units")

        tab_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Add container frame to notebook
        self.notebook.add(tab_container, text=name)

        # Store references using tab_frame as the key for caller compatibility
        self.tabs[tab_frame] = {
            "container": tab_container,
            "canvas": tab_canvas,
            "name": name,
            "filepath": None,
            "dirty": False,
        }

        # Set active tab and return the inner tab_frame
        self.notebook.select(tab_container)
        return tab_frame

    # Remove a tab entirely (used when loading replaces an empty first tab,
    # and by the "delete" button)
    def _remove_tab(self, tab_id=None):
        if tab_id is None or isinstance(tab_id, tk.Event):
            tab_id = self._get_active_tab_id()

        if tab_id is None or tab_id not in self.tabs:
            raise ValueError("No tab to remove.")

        tab_data = self.tabs.pop(tab_id)
        container = tab_data["container"]
        self.notebook.forget(container)
        container.destroy()

    # Open a popup to confirm if the user wants to delete a project tab.
    def _open_delete_tab_popup(self, event=None):
        if len(self.notebook.children) == 0:
            messagebox.showwarning("Warning", "No project tabs to delete!", parent=self.root)
            return

        popup = widgets.create_popup(self.root, "Delete Project Tab", 320, 150)

        confirmation_message = tk.Message(
            popup,
            text=f"Are you sure you want to delete the current project tab?\n\nAll unsave swatches will be lost.",
            font=("futura-book", 14),
            bg=cl.CC_WHITE,
            fg=cl.CC_BLACK,
            width=300)
        confirmation_message.grid(row=0, column=0, sticky="ew")

        btn_frame = tk.Frame(popup, bg=cl.CC_WHITE)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        btn_frame.columnconfigure(1, weight=1)

        def confirm(event=None):
            try:
                self.delete_active_tab()
            except ValueError:
                messagebox.showwarning("Warning", "No project tabs to delete!", parent=popup)
                return
            
            popup.destroy()

        def destroy_popup(self=None, event=None):
            popup.destroy()

        btn_close = tk.Button(btn_frame, text="Cancel", highlightbackground=cl.CC_WHITE, font=("futura-book", 12), command=destroy_popup)
        btn_close.grid(row=0, column=0, padx=10, pady=0)

        btn_create = tk.Button(btn_frame, text="Confirm", highlightbackground=cl.CC_WHITE, font=("futura-book", 12), command=confirm)
        btn_create.grid(row=0, column=2, padx=10, pady=0)

        popup.bind("<Return>", confirm)
        popup.bind("<Escape>", destroy_popup)

    # The frame currently shown by the Notebook, or None if there are no tabs
    def _get_active_tab_id(self):
        selection = self.notebook.select()

        if not selection:
            return None
        
        container = self.root.nametowidget(selection)
        for tab_frame, tab_data in self.tabs.items():
            if tab_data.get("container") == container:
                return tab_frame
            
        return None

    # Mark a tab as having unsaved changes and update its label with a "*"
    def _mark_dirty(self, tab_id):
        self.tabs[tab_id]["dirty"] = True
        self._update_tab_label(tab_id)

    def _update_tab_label(self, tab_id):
        if tab_id not in self.tabs:
            return
        
        tab = self.tabs[tab_id]
        label = tab["name"] + ("*" if tab["dirty"] else "")
        self.notebook.tab(tab["container"], text=label)

    '''
    SWATCH MANAGEMENT
    '''
    # Update swatch label to reflect the format in the menu combobox
    def update_all_swatches_label(self, event=None):
        # get the value of the format combobox
        format_value = self.format_combobox.get()

        # Remove focus from the combobox
        self._focus_main_window()
        
        # Loop through each tab id and then all of the swatches in each open tab
        for tab in list(self.tabs.keys()):
            if not tab.winfo_exists():
                continue
            swatches = [w for w in tab.winfo_children() if isinstance(w, widgets.Swatch)]
            for swatch in swatches:
                swatch.update_colour_code_label(format_value)
                swatch.active_format = format_value

    # Add a swatch into the active tab
    def _add_swatch_to_tab(self, tab_id, label_text, hex_code, mark_dirty=True, update_grid=True):
        widgets.Swatch(
            tab_id,
            app_root      = self.root,
            label_text    = label_text,
            hex_code      = hex_code,
            on_delete     = lambda: self._on_swatch_removed(tab_id),
            on_reorder    = lambda: self._on_swatch_reordered(tab_id),
            active_format = self._get_active_format()
        )  # raises ValueError for an invalid hex code

        if update_grid:
            self._regrid_tab(tab_id)

        if mark_dirty:
            self._mark_dirty(tab_id)

    def _on_swatch_reordered(self, tab_id):
        self._regrid_tab(tab_id)
        self._mark_dirty(tab_id)

    # Re-lay-out swatches sequentially, keeping the "+" button at the end
    def _regrid_tab(self, tab_id):
        swatches = [w for w in tab_id.winfo_children() if isinstance(w, widgets.Swatch)]

        tab_id.update_idletasks()

        # Get the width of the notebook tab frame in avoid swatches clipping out of view.
        notebook_width = self.notebook.winfo_width()

        # Defind padding amount
        pad_x = 5
        pad_y = 5

        # Keep track of how the grid is populating to allow multi-row layouts
        current_row       = 0
        current_column     = 0
        current_row_width = 0

        for swatch in swatches:
            # Get the swatch width and add it to the total row width
            swatch_width = swatch.winfo_reqwidth() + (pad_x * 4)

            # Compare the current row width with the notebook row to determine if this swatch should be on a new row
            if current_row_width + swatch_width > notebook_width and current_column > 0:
                current_row   += 1
                current_column = 0
                current_row_width = 0

            # Add the swatch to the correct row and column location
            swatch.grid(row=current_row, column=current_column, padx=pad_x, pady=pad_y, sticky="w")

            # Update variables for the next iteration
            current_row_width += swatch_width
            current_column    += 1

    def _on_swatch_removed(self, tab_id):
        self._regrid_tab(tab_id)
        self._mark_dirty(tab_id)

    # Collect a tab's swatches as plain dicts, ready for JSON export
    def _get_tab_swatches_data(self, tab_id):
        swatches = [w for w in tab_id.winfo_children() if isinstance(w, widgets.Swatch)]
        return [{"label": sw.label_text, "hex": sw.hex_code} for sw in swatches]

    # Get the active colour format from the drop down list
    def _get_active_format(self):
        return self.format_combobox.get()
    
    def get_active_tab_swatches(self):
        active_tab_id = self._get_active_tab_id()
        if active_tab_id is None:
            return None

        swatches = [w for w in active_tab_id.winfo_children() if isinstance(w, widgets.Swatch)]

        return swatches

    '''
    SAVE / LOAD
    '''

    # Save only the active tab's swatches to a JSON file wrapped in a custom file format .SWA
    # By default save as a .SWA as a JSON and the option for .ASE for Adobe software
    def save_active_tab(self, event=None):
        tab_id = self._get_active_tab_id()
        if tab_id is None:
            return

        tab = self.tabs[tab_id]
        data = {"name": tab["name"], "swatches": self._get_tab_swatches_data(tab_id)}

        filepath = tab["filepath"]
        if not filepath:
            filepath = filedialog.asksaveasfilename(
                title="Save Project Tab",
                defaultextension=".swa", # custom extension but with the structure of json inside
                filetypes=[
                    ("Swatch", "*.swa"),
                    ("JSON", "*.json")
                    ],
                initialfile=f"{tab['name']}.swa",
            )
            if not filepath:
                return  # user cancelled
            tab["filepath"] = filepath

        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            messagebox.showerror("Save Failed", f"Could not save file:\n{e}")
            return

        tab["dirty"] = False
        self._update_tab_label(tab_id)

    # Delete the active tab
    def delete_active_tab(self, event=None):
        tab_id = self._get_active_tab_id()

        if tab_id is None:
            return

        self._remove_tab(tab_id)

    # Load a previously saved JSON file into a new tab
    def load_project_tab(self, event=None):
        filepaths = filedialog.askopenfilenames(
            title="Load Project Tab",
            filetypes=[
                ("Swatch", "*.swa"),
                ("JSON", "*.json")
                ],
        )
        if not filepaths:
            return

        for file in filepaths:
            try:
                with open(file, "r") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                messagebox.showerror("Load Failed", f"Could not load file:\n{e}")
                return

            name = data.get("name", "untitled project")
            swatches = data.get("swatches", [])

            # On first launch there's just one empty, untouched default tab -
            # reuse it instead of leaving a redundant blank tab alongside.
            if len(self.tabs) == 1:
                (only_id,) = self.tabs.keys()
                only_tab = self.tabs[only_id]
                if not only_tab["dirty"] and only_tab["filepath"] is None and not self._get_tab_swatches_data(only_id):
                    self._remove_tab(only_id)

            tab_id = self._create_tab(name)
            for swatch in swatches:
                try:
                    self._add_swatch_to_tab(tab_id, swatch.get("label", ""), swatch.get("hex", "#FFFFFF"), mark_dirty=False, update_grid=False)
                except ValueError:
                    continue  # skip any malformed swatch entries
            
            # Update the tab's swatch grid
            self._regrid_tab(tab_id)

            self.tabs[tab_id]["filepath"] = file
            self.tabs[tab_id]["dirty"] = False
            self._update_tab_label(tab_id)

'''
TKINTER ENTRY POINT
'''
def on_closing():
    '''
    Open a popup when use clicks the window close button to confirm if they do want to quit the app.
    '''
    if messagebox.askokcancel("Quit", "Do you want to close the app? All unsaved projects will be lost!"):
        root.destroy()

root = tk.Tk()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.iconbitmap(get_resource_path("app_icon.ico"))
app = ColourCoperUI(root)
root.mainloop()