'''
The main UI for colour clipboard using tkinter as the graphical layer.
'''

import json
import mss
import os

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
        dropper_icon = Image.open("icons/dropper.png")
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
        self.tint_entry = tk.Entry(self.header_frame, width=5,highlightbackground=cl.CC_WHITE)
        self.tint_entry.insert(0, "100%")  # Pre-fill with hashtag as a helper
        self.tint_entry.grid(row=0, column=0)
        self.tint_entry.bind("<FocusOut>", self.update_swatch_tint)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.tint_entry, text="Update Tint/Shade: -95 to 100")

        # Colour code format dropdown
        # Dropdown options  
        self.colour_codes = ["hex", "rgb", "cmyk", "hsl"]

        self.format_combobox = ttk.Combobox(self.header_frame, values=self.colour_codes, width=5, state="readonly")
        self.format_combobox.set("hex")
        self.format_combobox.grid(row=0, column=1)
        self.format_combobox.bind("<<ComboboxSelected>>", self.update_all_swatches_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.format_combobox, text="Change colour format")

        # Eyedropper tool to create a swatch
        dropper_icon = Image.open("icons/dropper.png")
        dropper_icon = dropper_icon.resize((12,12))
        self.eyedrop_icon = ImageTk.PhotoImage(dropper_icon)

        self.eyedrop_button_border = tk.Frame(
            self.header_frame,
            bg=cl.CC_LIGHT_GREY,
            padx=1,
            pady=1
        )
        self.eyedrop_button_border.grid(row=0, column=2, padx=4)

        self.eyedrop_button = tk.Label(
            self.eyedrop_button_border,
            image=self.eyedrop_icon,
            highlightbackground=cl.CC_WHITE,
            bg=cl.CC_PURE_WHITE,
            )
        self.eyedrop_button.pack(ipadx=4, ipady=4)

        # Bind the new swatch button
        self.eyedrop_button.bind("<Button-1>", lambda event: self.start_eyedropper())
        self.eyedrop_button.bind("<Enter>", self.on_hover_label)
        self.eyedrop_button.bind("<Leave>", self.on_leave_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.eyedrop_button, text="Create swatch from an eyedrop")

        # Add a new swatch to the active tab
        new_swatch_icon = Image.open("icons/plus.png")
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
            text="  swatch",
            image=self.new_swatch_image,
            highlightbackground=cl.CC_WHITE,
            bg=cl.CC_PURE_WHITE,
            fg=cl.CC_BLACK,
            compound="left"
            )
        self.new_swatch_button.pack(ipadx=4, ipady=4)

        # Bind the new swatch button
        self.new_swatch_button.bind("<Button-1>", lambda event: self.add_new_swatch())
        self.new_swatch_button.bind("<Enter>", self.on_hover_label)
        self.new_swatch_button.bind("<Leave>", self.on_leave_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.new_swatch_button, text="Add new swatch")

        # Add a new tab for swatches.
        new_folder_icon = Image.open("icons/folder-plus.png")
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
            compound="left",
            )
        self.add_notebook.pack(ipadx=4, ipady=4)

        # Bind the new project button
        self.add_notebook.bind("<Button-1>", lambda event: self.add_new_project_tab())
        self.add_notebook.bind("<Enter>", self.on_hover_label)
        self.add_notebook.bind("<Leave>", self.on_leave_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.add_notebook, text="Add new project")

        # Save swatch palette button aligned to the right of the window.
        save_icon = Image.open("icons/save-01.png")
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
            pady=5
            )
        self.save_button.pack(ipadx=4, ipady=4)

        # Bind the save button
        self.save_button.bind("<Button-1>", lambda event: self.save_active_tab())
        self.save_button.bind("<Enter>", self.on_hover_label)
        self.save_button.bind("<Leave>", self.on_leave_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(self.save_button, text="Save project")

        # Load swatches palette button aligned to the right of the window.
        load_icon = Image.open("icons/folder-open.png")
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
        widgets.CursorFollowerLabel(self.load_button, text="Open a project")

        # Delete swatches palette button aligned to the right of the window.
        delete_icon = Image.open("icons/trash.png")
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
        widgets.CursorFollowerLabel(self.delete_palette_button, text="Delete project")

        '''
        TAB SECTION

        |[project tab] [project tab] [+]        |
        '''
        # The Notebook control handles tab buttons, switching, and active
        # styling automatically - we just add/remove/rename its child frames.
        self.notebook = ttk.Notebook(self.tab_frame)
        self.notebook.pack(side = "left", fill = "both", expand = True, pady = 10)


        '''
        FOOTER SECTION
        '''
        # Configure column 1 to expand and create white space.
        self.footer_frame.columnconfigure(0, weight=2)
        self.footer_frame.columnconfigure(2, weight=2)

        footer_text = widgets.LabelFooter(self.footer_frame, text = "Designed & Developed by Kelton Boyter-Grant", bg = cl.CC_WHITE)
        footer_text.grid(row=0, column=1, padx=20, pady=(0, 20))

        # Contains some helpful information for first time users if they need it.
        self.help_button = tk.Button(self.footer_frame, text="?", highlightbackground=cl.CC_WHITE, command=self.open_help_popup)
        self.help_button.grid(row=0, column=3, pady=(0,20), padx=0)

        '''
        KEYBOARD BINDINGS
        '''
        # Save the active tab swatches
        self.root.bind("<Command-s>", self.save_active_tab)
        self.root.bind("<Command-S>", self.save_active_tab)

        # Delete the active tab
        self.root.bind("<Command-d>", self._open_delete_tab_popup)
        self.root.bind("<Command-D>", self._open_delete_tab_popup)

        # Load a swatch file
        self.root.bind("<Command-o>", self.load_project_tab)
        self.root.bind("<Command-O>", self.load_project_tab)

        # Add a new swatch
        self.root.bind("<Command-n>", self.add_new_swatch)
        self.root.bind("<Command-N>", self.add_new_swatch)

        # Cycle the dropdown box of colour formats
        self.root.bind("<Command-f>", self.cycle_colour_format)
        self.root.bind("<Command-F>", self.cycle_colour_format)

        # Create a new project tab
        self.root.bind("<Command-p>", self.add_new_project_tab)
        self.root.bind("<Command-P>", self.add_new_project_tab)

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
        popup = widgets.create_popup(self.root, "Add Swatch", 260, 260)

        # POPUP LAYOUT
        # Configure layout spacing for the popup
        popup.columnconfigure(1, weight=1)
        popup.config(padx=15, pady=15)

        # Colour preview
        colour_preview = tk.Frame(
            popup,
            background="#ff0000",
            height=75
        )
        colour_preview.grid(row=0, column=0, rowspan=2, columnspan=3, sticky="nesw", pady=5)

        # Name Entry Widget
        lbl_name = tk.Label(popup, text="Name:", bg=cl.CC_WHITE)
        lbl_name.grid(row=2, column=0, sticky="w", pady=5)
        
        ent_name = tk.Entry(popup, bg=cl.CC_WHITE)
        ent_name.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=5)
        ent_name.focus_set()  # Automatically place cursor in this box

        # Hex Entry Widget
        lbl_hex = tk.Label(popup, text="Hex Code: #", bg=cl.CC_WHITE)
        lbl_hex.grid(row=3, column=0, sticky="w", pady=5)
        
        ent_hex = tk.Entry(popup, bg=cl.CC_WHITE)
        ent_hex.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=5)

        # Bind every key press to check if a hex code has been supplied to update the colour preview
        def update_colour_preview(self):
                    hex_code = ent_hex.get().strip()
                    if len(hex_code) != 6:
                        return

                    # Try to update the preview frame background colour.
                    try:
                        colour_preview.config(bg=f"#{hex_code}")
                    except _tkinter.TclError:
                        messagebox.showwarning("Warning", "Please enter a valid hex code, e.g. #FF8D28", parent=popup)
                        return
                    
        ent_hex.bind("<KeyRelease>", update_colour_preview)

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
        eyedrop_button.pack(ipadx=4, ipady=4)

        # Bind the new swatch button
        eyedrop_button.bind("<Button-1>", lambda event: self.start_eyedropper())
        self.eyedrop_button.bind("<Enter>", self.on_hover_label)
        eyedrop_button.bind("<Leave>", self.on_leave_label)

        # Add the hover label class
        widgets.CursorFollowerLabel(eyedrop_button, text="Create swatch from an eyedrop")

        if hex:
            ent_hex.insert(0, hex)

        #  BUTTON FUNCTIONS
        def save_action():
            name_data = ent_name.get().strip().capitalize()
            hex_data  = ent_hex.get().strip()

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
                hex_data = f"#{hex_data}"

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
        btn_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(20, 0))
        btn_frame.columnconfigure(0, weight=1) # Invisible space pushing buttons right

        # Close Button
        btn_close = tk.Button(btn_frame, text="Close", bg=cl.CC_WHITE, command=popup.destroy)  # [3]
        btn_close.grid(row=0, column=1, padx=5)

        # Save Button
        btn_save = tk.Button(btn_frame, text="Save", bg=cl.CC_WHITE, command=save_action)
        btn_save.grid(row=0, column=2, padx=5)

        # Bind keyboard inputs
        popup.bind("<Return>", _save_action_shortcut)
        popup.bind("<Escape>", close_popup)

    # Create a new, empty project tab via a name-entry pop-up
    def add_new_project_tab(self, event=None):
        popup = tk.Toplevel(self.root)
        popup.title("New Project Tab")
        popup.transient(self.root)
        popup.grab_set()
        popup.columnconfigure(1, weight=1)
        popup.config(padx=15, pady=15)
        popup.resizable(False, False)

        # Open the popup in the centre of the root window.
        widgets.centre_launch_popup(self.root, popup, 300, 130)

        lbl_name = tk.Label(popup, text="Project Name:")
        lbl_name.grid(row=0, column=0, sticky="w", pady=5)

        ent_name = tk.Entry(popup)
        ent_name.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        ent_name.focus_set()

        def create_action(event=None):
            name = ent_name.get().strip()
            if not name:
                messagebox.showwarning("Warning", "Please enter a project name!", parent=popup)
                return
            self._create_tab(name)
            popup.destroy()
        
        def close_popup(self):
            popup.destroy()


        btn_frame = tk.Frame(popup)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        btn_frame.columnconfigure(0, weight=1)

        btn_close = tk.Button(btn_frame, text="Cancel", command=popup.destroy)
        btn_close.grid(row=0, column=1, padx=5, pady=0)

        btn_create = tk.Button(btn_frame, text="Create", command=create_action)
        btn_create.grid(row=0, column=2, padx=5, pady=0)

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

        self.tint_entry.delete(0, "end")
        if tint_value == 0:
            # Setting to 0 will be pure white, reset to the original colour
            self.tint_entry.insert(0, "100%")
            tint_value = 100
        else:
            self.tint_entry.insert(0, f"{tint_value}%")

        for tab_frame, tab_data in self.tabs.items():
            swatches = tab_frame.winfo_children()
            if swatches:
                for swatch in swatches:
                    swatch.update_colour_tint(int(tint_value))

    # EYEDROPPER FUNCTIONS
    def start_eyedropper(self):
        if len(self.notebook.children) == 0:
            messagebox.showwarning("Warning", "No project tabs to add swatch to!", parent=self.root)
            return
        # Hide the main window so it doesn't appear in the screenshot
        self.root.withdraw()
        
        # Force a UI update and add a tiny delay to ensure the window is hidden
        self.root.update()
        self.root.after(50, self.take_screenshot_and_show_overlay)

    def take_screenshot_and_show_overlay(self):
        # Capture the entire screen
        # self.screen_img = ImageGrab.grab(scale_down=True)

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            
            # 1. Get the raw image as usual
            raw_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            # 2. Define the path to the standard macOS Display P3 profile
            p3_profile_path = "/System/Library/ColorSync/Profiles/Display P3.icc"
            
            # 3. Check if the profile exists (standard on modern Macs) and convert
            if os.path.exists(p3_profile_path):
                try:
                    # Load the Mac's P3 profile and Pillow's built-in sRGB profile
                    p3_profile = ImageCms.ImageCmsProfile(p3_profile_path)
                    srgb_profile = ImageCms.createProfile("sRGB")
                    
                    # Build the conversion matrix
                    transform = ImageCms.buildTransform(
                        inputProfile=p3_profile, 
                        outputProfile=srgb_profile, 
                        inMode="RGB", 
                        outMode="RGB"
                    )
                    
                    # Apply the transformation to the screenshot
                    self.screen_img = ImageCms.applyTransform(raw_img, transform)
                    
                except Exception as e:
                    print(f"Color conversion failed: {e}")
                    self.screen_img = raw_img
            else:
                print("P3 ICC profile not found, skipping conversion.")
                self.screen_img = raw_img

        # Create a fullscreen, borderless overlay window
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-topmost", True) # Keep it above all other apps
        self.overlay.config(cursor="crosshair")   # Change cursor to a crosshair

        # Display the screenshot on a Canvas
        self.tk_img = ImageTk.PhotoImage(self.screen_img)

        screen_width  = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.canvas = tk.Canvas(self.overlay, highlightthickness=0, width=screen_width, height=screen_height)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")

        # Bind the left mouse click to our selection method
        self.canvas.bind("<Button-1>", self.on_pixel_click)
        
        # Bind Escape key to cancel
        self.overlay.bind("<Escape>", lambda e: self.close_overlay())

    def on_pixel_click(self, event):
        # Get the exact x, y coordinates of the click
        # x, y = event.x, event.y

        scale_factor = self.screen_img.width / self.root.winfo_screenwidth()
    
        # Scale the Tkinter event coordinates to match the mss physical pixels
        actual_x = int(event.x * scale_factor)
        actual_y = int(event.y * scale_factor)
        
        # Grab the RGB color at those coordinates from our captured image
        pixel_color = self.screen_img.getpixel((actual_x, actual_y))
        r, g, b = pixel_color[:3]

        # Close the overlay and restore the main window
        self.close_overlay()

        # Call your custom function with the selected color
        self.open_swatch_popup(self._get_active_tab_id(), rgb_to_hex(r,g,b))

    def close_overlay(self):
        self.overlay.destroy()
        self.root.deiconify() # Bring the main window back

    '''
    TAB MANAGEMENT
    '''

    # Create a new tab (content frame + "+" swatch button) and switch to it.
    # The frame itself is used as the tab's identifier throughout, since
    # that's what ttk.Notebook expects.
    def _create_tab(self, name):
        tab_frame = tk.Frame(self.notebook, bg=cl.CC_WHITE)
        self.notebook.add(tab_frame, text=name)

        self.tabs[tab_frame] = {
            "name": name,
            "filepath": None,
            "dirty": False,
        }

        self.notebook.select(tab_frame)
        return tab_frame

    # Remove a tab entirely (used when loading replaces an empty first tab,
    # and by the "delete" button)
    def _remove_tab(self, event=None):
        active_tab_id = self._get_active_tab_id()

        if active_tab_id is None:
            raise ValueError

        self.tabs.pop(active_tab_id, None)
        self.notebook.forget(active_tab_id)
        active_tab_id.destroy()

    # Open a popup to confirm if the user wants to delete a project tab.
    def _open_delete_tab_popup(self, event=None):
        if len(self.notebook.children) == 0:
            messagebox.showwarning("Warning", "No project tabs to delete!", parent=self.root)
            return

        popup = widgets.create_popup(self.root, "Delete Project Tab", 300, 130)

        confirmation_message = tk.Message(popup, text=f"Are you sure you want to delete the current project tab?\nAll unsave swatches will be lost.", font=("Arial", 14), bg=cl.CC_WHITE, fg=cl.CC_BLACK, width=280)
        confirmation_message.grid(row=0, column=0, sticky="w", pady=5, padx=10)

        btn_frame = tk.Frame(popup, bg=cl.CC_WHITE)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(20, 10), padx=10)
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

        btn_close = tk.Button(btn_frame, text="Cancel", highlightbackground=cl.CC_WHITE, command=destroy_popup)
        btn_close.grid(row=0, column=0, padx=10, pady=0)

        btn_create = tk.Button(btn_frame, text="Confirm", highlightbackground=cl.CC_WHITE, command=confirm)
        btn_create.grid(row=0, column=2, padx=10, pady=0)

        popup.bind("<Return>", confirm)
        popup.bind("<Escape>", destroy_popup)

    # The frame currently shown by the Notebook, or None if there are no tabs
    def _get_active_tab_id(self):
        selection = self.notebook.select()
        if not selection:
            return None
        return self.root.nametowidget(selection)

    # Mark a tab as having unsaved changes and update its label with a "*"
    def _mark_dirty(self, tab_id):
        self.tabs[tab_id]["dirty"] = True
        self._update_tab_label(tab_id)

    def _update_tab_label(self, tab_id):
        tab = self.tabs[tab_id]
        label = tab["name"] + ("*" if tab["dirty"] else "")
        self.notebook.tab(tab_id, text=label)

    '''
    SWATCH MANAGEMENT
    '''

    # Update swatch label to reflect the format in the menu combobox
    def update_all_swatches_label(self, event=None):
        # get the value of the format combobox
        format_value = self.format_combobox.get()
        
        # Loop through each tab id and then all of the swatches in each open tab
        for tab in self.tabs:
            # Get all of the swatches inside the tab to update the labels on.
            swatches = [w for w in tab.winfo_children() if isinstance(w, widgets.Swatch)]
            # Update each swatch's label text with the new colour code format.
            for i, swatch in enumerate(swatches):
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
    HELP BUTTON POPUP
    '''
    def open_help_popup(self, event=None):
        # Create the top-level pop-up window
        popup = tk.Toplevel(self.root, bg=cl.CC_WHITE)
        popup.title("Information")
        popup.resizable(False, False)

        # Launch the popup in the centre of the root window.
        widgets.centre_launch_popup(self.root ,popup, 400, 260)
        
        # Make the popup modal (blocks interaction with main window)
        popup.transient(self.root)   # Keeps popup on top of main window [2]
        popup.grab_set()             # Directs all events to this window [1, 3]

        # List of information
        information_text = (f"Swatch is an app focused on colour management "
                             "across design disiplines to help organise "
                             "the project colour palettes.")

        popup_heading = tk.Message(popup, text=information_text, font=("Arial", 14), bg=cl.CC_WHITE, fg=cl.CC_BLACK, width=370)
        popup_heading.pack(anchor="nw", padx=20, pady=(20,0), expand=True)

        # Keyboard shortcuts
        keyboard_shortcuts_heading = tk.Message(popup, text="Keyboard shortcuts", font=("Arial", 14, "bold"), bg=cl.CC_WHITE, fg=cl.CC_BLACK, width=380)
        keyboard_shortcuts_heading.pack(anchor="nw", padx=20, pady=0, expand=True)

        keyboard_shortcuts = ("• Save: ⌘ + s\n"
                             "• Load: ⌘ + o\n"
                             "• New project tab: ⌘ + p\n"
                             "• New swatch: ⌘ + n\n"
                             "• Cycle colour formats: ⌘ + f\n")
        
        keyboard_shortcuts_label = tk.Message(popup, text=keyboard_shortcuts, font=("Arial", 14), bg=cl.CC_WHITE, fg=cl.CC_BLACK, width=380)
        keyboard_shortcuts_label.pack(anchor="nw", padx=20, pady=0, expand=True)

        # Close button
        btn_close = tk.Button(popup, text="Close", highlightbackground=cl.CC_WHITE, command=popup.destroy)
        btn_close.pack(padx=20, pady=(0,20), anchor="sw")

        def close_popup(self):
            popup.destroy()

        # Keyboard bindings
        popup.bind("<Escape>", close_popup)
        popup.bind("<Return>", close_popup)

'''
TKINTER ENTRY POINT
'''
root = tk.Tk()
app = ColourCoperUI(root)
root.mainloop()