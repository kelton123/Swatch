'''
The main UI for colour clipboard using tkinter as the graphical layer.
'''

import json

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

import widgets as widgets
import colours as cl


'''
CONSTANTS
'''
WINDOW_PADDING = 40
DATA_FILE = "swatches.json"
        

class ColourCoperUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Swatch")
        self.root.geometry("960x540")
        self.root.minsize(854,480)
        self.root.config(background = cl.CC_WHITE)
        self.root.resizable(False, False)

        self.centre_launch(self.root)

        # Tracks every open project tab, keyed by its content frame (the
        # widget the Notebook uses as the tab's identifier): frame ->
        # {name, add_button, filepath, dirty}. Each tab is its own
        # "document", saved/loaded independently (like tabs in Illustrator).
        # The Notebook widget itself is the single source of truth for
        # which tab is active and how tabs are displayed/switched.
        self.tabs = {}

        '''
        LAYOUT
        '''
        # Header section with project name, save and import buttons.
        self.header_frame = tk.Frame(root, height = 100, bg = cl.CC_WHITE)
        self.header_frame.pack(side = "top", fill = "x", padx = WINDOW_PADDING)

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
        # Configure column 1 to expand and create white space.
        self.header_frame.columnconfigure(1, weight=2)
        self.header_frame.columnconfigure(5, weight=2)

        # Project name label aligned to the left of the window.
        self.project_heading = widgets.LabelHeading(self.header_frame, text = "Swatch")
        self.project_heading.grid(row = 0, column = 0, sticky = "w", pady = 20)

        # SWATCH TOOLS
        # Add a new tab for swatches.
        self.add_notebook = tk.Button(self.header_frame, text="add", highlightbackground = cl.CC_WHITE, command=self.add_new_swatch)
        self.add_notebook.grid(row=0, column=2)

        # Tint adjustment
        self.tint_entry = tk.Entry(self.header_frame, width=5,highlightbackground=cl.CC_WHITE)
        self.tint_entry.insert(0, "100%")  # Pre-fill with hashtag as a helper
        self.tint_entry.grid(row=0, column=3)

        # Colour code format dropdown
        # Dropdown options  
        self.colour_codes = ["hex", "rgb", "cmyk", "hsl", "css"]

        self.format_combobox = ttk.Combobox(self.header_frame, values=self.colour_codes, width=5, state="readonly")
        self.format_combobox.set("hex")
        self.format_combobox.grid(row=0, column=4)
        self.format_combobox.bind("<<ComboboxSelected>>", self.update_all_swatches_label)

        # Add a new tab for swatches.
        self.add_notebook = tk.Button(self.header_frame, text="new", highlightbackground = cl.CC_WHITE, command=self.new_project_tab)
        self.add_notebook.grid(row=0, column=6)

        # Save swatch palette button aligned to the right of the window.
        self.save_button = tk.Button(self.header_frame, highlightbackground = cl.CC_WHITE, text = "save", command = self.save_active_tab)
        self.save_button.grid(row = 0, column = 7)

        # Load swatches palette button aligned to the right of the window.
        self.load_button = tk.Button(self.header_frame, highlightbackground = cl.CC_WHITE, text = "load", command = self.load_project_tab)
        self.load_button.grid(row = 0, column = 8)

        # Delete swatches palette button aligned to the right of the window.
        self.delete_palette_button = tk.Button(self.header_frame, highlightbackground=cl.CC_WHITE, text="delete", command=self.delete_active_tab)
        self.delete_palette_button.grid(row=0, column=9)

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
        footer_text = widgets.LabelFooter(self.footer_frame, text = "Designed & Developed by Kelton Boyter-Grant", bg = cl.CC_WHITE)
        footer_text.pack(padx=20, pady=20, anchor="center")


    '''
    UI FUNCTIONS
    '''
    # Launch the window in the centre of the screen.
    def centre_launch(self, window, window_width=960, window_height=540):
        center_x, center_y = self.get_screen_centre()

        # set the position of the window to the center of the screen
        window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    def centre_launch_popup(self, window, window_width, window_height):
        # Get the current position and size of the root window
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        # Calculate the exact offsets to center the popup
        x_coord = int(root_x + (root_width - window_width) / 2)
        y_coord = int(root_y + (root_height - window_height) / 2)
        
        # Apply the geometry string (coordinates must be integers)
        window.geometry(f"{window_width}x{window_height}+{x_coord}+{y_coord}")

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


    # Add a new swatch in the active tab
    def add_new_swatch(self):
        active_tab_id = self._get_active_tab_id()
        self.open_swatch_popup(active_tab_id)

    # Create a new swatch inside the given tab
    def open_swatch_popup(self, tab_id):
        # 1. Create the top-level pop-up window
        popup = tk.Toplevel(self.root)
        popup.title("Add Swatch")
        popup.resizable(False, False)

        # Launch the popup in the centre of the root window.
        self.centre_launch_popup(popup, 260, 150)
        
        # Make the popup modal (blocks interaction with main window)
        popup.transient(self.root)   # Keeps popup on top of main window [2]
        popup.grab_set()             # Directs all events to this window [1, 3]
        
        # Configure layout spacing for the popup
        popup.columnconfigure(1, weight=1)
        popup.config(padx=15, pady=15)

        # 2. Name Entry Widget
        lbl_name = tk.Label(popup, text="Name:")
        lbl_name.grid(row=0, column=0, sticky="w", pady=5)
        
        ent_name = tk.Entry(popup)
        ent_name.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        ent_name.focus_set()  # Automatically place cursor in this box

        # 3. Hex Entry Widget
        lbl_hex = tk.Label(popup, text="Hex Code: #")
        lbl_hex.grid(row=1, column=0, sticky="w", pady=5)
        
        ent_hex = tk.Entry(popup)
        ent_hex.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)

        # 4. Action Functions
        def save_action():
            name_data = ent_name.get().strip()
            hex_data = f"#{ent_hex.get().strip()}"
            
            # Simple validation check
            if not name_data or not hex_data:
                messagebox.showwarning("Warning", "Both fields are required!", parent=popup)
                return
                
            # Create a new swatch widget from the user's input values.
            try:
                self._add_swatch_to_tab(tab_id, name_data, hex_data)
            except ValueError:
                messagebox.showwarning("Warning", "Please enter a valid hex code, e.g. #FF8D28", parent=popup)
                return

            popup.destroy()  # Close the popup window after saving [3]

        def _save_action_shortcut(slef):
            save_action()

        def close_popup(self):
            popup.destroy()

        # 5. Buttons Layout Frame (at the bottom)
        btn_frame = tk.Frame(popup)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        btn_frame.columnconfigure(0, weight=1) # Invisible space pushing buttons right

        # Close Button
        btn_close = tk.Button(btn_frame, text="Close", command=popup.destroy)  # [3]
        btn_close.grid(row=0, column=1, padx=5)

        # Save Button
        btn_save = tk.Button(btn_frame, text="Save", command=save_action)
        btn_save.grid(row=0, column=2, padx=5)

        # Bind keyboard inputs
        popup.bind("<Return>", _save_action_shortcut)
        popup.bind("<Escape>", close_popup)

    # Create a new, empty project tab via a name-entry pop-up
    def new_project_tab(self):
        popup = tk.Toplevel(self.root)
        popup.title("New Project Tab")
        popup.transient(self.root)
        popup.grab_set()
        popup.columnconfigure(1, weight=1)
        popup.config(padx=15, pady=15)
        popup.resizable(False, False)

        # Open the popup in the centre of the root window.
        self.centre_launch_popup(popup, 300, 130)

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
    def _remove_tab(self, tab_id):
        self.tabs.pop(tab_id, None)
        self.notebook.forget(tab_id)
        tab_id.destroy()

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
    def update_all_swatches_label(self, event):
        # get the value of the format combobox
        format_value = event.widget.get()
        
        # Loop through each tab id and then all of the swatches in each open tab
        for tab in self.tabs:
            # Get all of the swatches inside the tab to update the labels on.
            swatches = [w for w in tab.winfo_children() if isinstance(w, widgets.Swatch)]
            # Update each swatch's label text with the new colour code format.
            for i, swatch in enumerate(swatches):
                swatch.update_colour_code_label(format_value)

    # Add a swatch into the active tab
    def _add_swatch_to_tab(self, tab_id, label_text, hex_code, mark_dirty=True):
        widgets.Swatch(
            tab_id,
            label_text=label_text,
            hex_code=hex_code,
            on_delete=lambda: self._on_swatch_removed(tab_id),
        )  # raises ValueError for an invalid hex code
        
        self._regrid_tab(tab_id)
        if mark_dirty:
            self._mark_dirty(tab_id)

    # Re-lay-out swatches sequentially, keeping the "+" button at the end
    def _regrid_tab(self, tab_id):
        tab = self.tabs[tab_id]
        swatches = [w for w in tab_id.winfo_children() if isinstance(w, widgets.Swatch)]
        for i, swatch in enumerate(swatches):
            swatch.grid(row=0, column=i, padx=5, pady=5)

    def _on_swatch_removed(self, tab_id):
        self._regrid_tab(tab_id)
        self._mark_dirty(tab_id)

    # Collect a tab's swatches as plain dicts, ready for JSON export
    def _get_tab_swatches_data(self, tab_id):
        swatches = [w for w in tab_id.winfo_children() if isinstance(w, widgets.Swatch)]
        return [{"label": sw.label_text, "hex": sw.hex_code} for sw in swatches]

    '''
    SAVE / LOAD
    '''

    # Save only the active tab's swatches to a JSON file
    def save_active_tab(self):
        tab_id = self._get_active_tab_id()
        if tab_id is None:
            return

        tab = self.tabs[tab_id]
        data = {"name": tab["name"], "swatches": self._get_tab_swatches_data(tab_id)}

        filepath = tab["filepath"]
        if not filepath:
            filepath = filedialog.asksaveasfilename(
                title="Save Project Tab",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                initialfile=f"{tab['name']}.json",
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
    def delete_active_tab(self):
        tab_id = self._get_active_tab_id()
        if tab_id is None:
            return

        self._remove_tab(tab_id)

    # Load a previously saved JSON file into a new tab
    def load_project_tab(self):
        filepath = filedialog.askopenfilename(
            title="Load Project Tab",
            filetypes=[("JSON files", "*.json")],
        )
        if not filepath:
            return

        try:
            with open(filepath, "r") as f:
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
                self._add_swatch_to_tab(tab_id, swatch.get("label", ""), swatch.get("hex", "#FFFFFF"), mark_dirty=False)
            except ValueError:
                continue  # skip any malformed swatch entries

        self.tabs[tab_id]["filepath"] = filepath
        self.tabs[tab_id]["dirty"] = False
        self._update_tab_label(tab_id)


'''
TKINTER ENTRY POINT
'''
root = tk.Tk()
app = ColourCoperUI(root)
root.mainloop()