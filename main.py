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

        # Tracks every open project tab: tab_id -> {name, button, frame,
        # add_button, filepath, dirty}. Each tab is its own "document",
        # saved/loaded independently (like tabs in Illustrator).
        self.tabs = {}
        self.active_tab_id = None
        self._tab_counter = 0

        '''
        LAYOUT
        '''
        # Header section with project name, save and import buttons.
        self.header_frame = tk.Frame(root, height = 100, bg = cl.CC_WHITE)
        self.header_frame.pack(side = "top", fill = "x", padx = WINDOW_PADDING)

        # Tab section with buttons for each colour swatch group.
        self.tab_frame = tk.Frame(root, height = 50, bg = cl.CC_WHITE)
        self.tab_frame.pack(side = "top", fill = "x", padx = WINDOW_PADDING, pady = (0, 20))

        # Swatches section with all of the swatch cards.
        self.swatches_frame = tk.Frame(root, height = 100, bg = cl.CC_WHITE)
        self.swatches_frame.pack(side = "top", fill = "both", expand = True, padx = WINDOW_PADDING)

        # Footer section
        self.footer_frame = tk.Frame(root, height = 50, bg = cl.CC_WHITE)
        self.footer_frame.pack(side = "bottom", fill = "x", padx = WINDOW_PADDING)


        '''
        HEADER SECTION
        
        |[project name]                 [save][load]|
        '''
        # Configure column 1 to expand and create white space.
        self.header_frame.columnconfigure(1, weight=1)

        # Project name label aligned to the left of the window.
        self.project_heading = widgets.LabelHeading(self.header_frame, text = "Swatch")
        self.project_heading.grid(row = 0, column = 0, sticky = "w", pady = 20)

        # Save swatch palette button aligned to the right of the window.
        self.save_button = tk.Button(self.header_frame, highlightbackground = cl.CC_WHITE, text = "save", command = self.save_active_tab)
        self.save_button.grid(row = 0, column = 2)

        # Load swatches palette button aligned to the right of the window.
        self.load_button = tk.Button(self.header_frame, highlightbackground = cl.CC_WHITE, text = "load", command = self.load_project_tab)
        self.load_button.grid(row = 0, column = 3)

        '''
        TAB SECTION

        |[project tab] [project tab] [+]        |
        '''
        # New tab button (packed first so new tabs can insert themselves
        # to its left, keeping it as the rightmost "+" button).
        self.tab_button = widgets.ButtonNewTab(self.tab_frame, command = self.new_project_tab)
        self.tab_button.pack(side = "left", padx = (0, 10))


        '''
        FOOTER SECTION
        '''
        footer_text = widgets.LabelFooter(self.footer_frame, text = "Designed & Developed by Kelton Boyter-Grant", bg = cl.CC_WHITE)
        footer_text.pack(padx=20, pady=20, anchor="center")


    '''
    UI FUNCTIONS
    '''

    # Create a new swatch inside the given tab
    def open_swatch_popup(self, tab_id):
        # 1. Create the top-level pop-up window
        popup = tk.Toplevel(self.root)
        popup.title("Add Swatch")
        popup.geometry("300x180")
        
        # Make the popup modal (blocks interaction with main window)
        popup.transient(self.root)   # Keeps popup on top of main window [2]
        popup.grab_set()        # Directs all events to this window [1, 3]
        
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
        lbl_hex = tk.Label(popup, text="Hex Code:")
        lbl_hex.grid(row=1, column=0, sticky="w", pady=5)
        
        ent_hex = tk.Entry(popup)
        ent_hex.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)
        ent_hex.insert(0, "#")  # Pre-fill with hashtag as a helper

        # 4. Action Functions
        def save_action():
            name_data = ent_name.get().strip()
            hex_data = ent_hex.get().strip()
            
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

    # Create a new, empty project tab via a name-entry pop-up
    def new_project_tab(self):
        popup = tk.Toplevel(self.root)
        popup.title("New Project Tab")
        popup.geometry("300x140")
        popup.transient(self.root)
        popup.grab_set()
        popup.columnconfigure(1, weight=1)
        popup.config(padx=15, pady=15)

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

        ent_name.bind("<Return>", create_action)

        btn_frame = tk.Frame(popup)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        btn_frame.columnconfigure(0, weight=1)

        btn_close = tk.Button(btn_frame, text="Cancel", command=popup.destroy)
        btn_close.grid(row=0, column=1, padx=5)

        btn_create = tk.Button(btn_frame, text="Create", command=create_action)
        btn_create.grid(row=0, column=2, padx=5)

    '''
    TAB MANAGEMENT
    '''

    # Create a new tab (button + empty swatch palette) and switch to it
    def _create_tab(self, name):
        self._tab_counter += 1
        tab_id = self._tab_counter

        # Tab button, inserted just left of the "+" new-tab button.
        tab_button = widgets.ButtonTab(self.tab_frame, text=name)
        tab_button.config(command=lambda: self.switch_tab(tab_id))
        tab_button.pack(side="left", padx=(0, 10), before=self.tab_button)

        # Content frame that holds this tab's swatches. Only the active
        # tab's frame is packed/visible at any time.
        tab_content = tk.Frame(self.swatches_frame, bg=cl.CC_WHITE)

        add_button = widgets.ButtonNewSwatch(tab_content, command=lambda: self.open_swatch_popup(tab_id))
        add_button.grid(row=0, column=0, padx=5, pady=5)

        self.tabs[tab_id] = {
            "name": name,
            "button": tab_button,
            "frame": tab_content,
            "add_button": add_button,
            "filepath": None,
            "dirty": False,
        }

        self.switch_tab(tab_id)
        return tab_id

    # Remove a tab entirely (used when loading replaces an empty first tab)
    def _remove_tab(self, tab_id):
        tab = self.tabs.pop(tab_id)
        tab["button"].destroy()
        tab["frame"].destroy()
        if self.active_tab_id == tab_id:
            self.active_tab_id = None

    # Show the given tab's swatches and hide all others
    def switch_tab(self, tab_id):
        if tab_id == self.active_tab_id:
            return
        if self.active_tab_id in self.tabs:
            self.tabs[self.active_tab_id]["frame"].pack_forget()

        self.active_tab_id = tab_id
        self.tabs[tab_id]["frame"].pack(fill="both", expand=True)

        for tid, tab in self.tabs.items():
            tab["button"].set_active(tid == tab_id)

    # Mark a tab as having unsaved changes and update its label with a "*"
    def _mark_dirty(self, tab_id):
        self.tabs[tab_id]["dirty"] = True
        self._update_tab_label(tab_id)

    def _update_tab_label(self, tab_id):
        tab = self.tabs[tab_id]
        label = tab["name"] + ("*" if tab["dirty"] else "")
        tab["button"].config(text=label)

    '''
    SWATCH MANAGEMENT
    '''

    # Add a swatch into a tab and lay it out next to the tab's "+" button
    def _add_swatch_to_tab(self, tab_id, label_text, hex_code, mark_dirty=True):
        tab = self.tabs[tab_id]
        widgets.Swatch(
            tab["frame"],
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
        swatches = [w for w in tab["frame"].winfo_children() if isinstance(w, widgets.Swatch)]
        for i, swatch in enumerate(swatches):
            swatch.grid(row=0, column=i, padx=5, pady=5)
        tab["add_button"].grid(row=0, column=len(swatches), padx=5, pady=5)

    def _on_swatch_removed(self, tab_id):
        self._regrid_tab(tab_id)
        self._mark_dirty(tab_id)

    # Collect a tab's swatches as plain dicts, ready for JSON export
    def _get_tab_swatches_data(self, tab_id):
        frame = self.tabs[tab_id]["frame"]
        swatches = [w for w in frame.winfo_children() if isinstance(w, widgets.Swatch)]
        return [{"label": sw.label_text, "hex": sw.hex_code} for sw in swatches]

    '''
    SAVE / LOAD
    '''

    # Save only the active tab's swatches to a JSON file
    def save_active_tab(self):
        if self.active_tab_id is None:
            return

        tab = self.tabs[self.active_tab_id]
        data = {"name": tab["name"], "swatches": self._get_tab_swatches_data(self.active_tab_id)}

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
        self._update_tab_label(self.active_tab_id)

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