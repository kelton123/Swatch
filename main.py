'''
The main UI for colour clipboard using tkinter as the graphical layer.
'''

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

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
        self.root.title("Colour Clipboard")
        self.root.geometry("960x540")
        self.root.minsize(854,480)
        self.root.config(background = cl.CC_WHITE)
        self.root.resizable(False, False)

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
        self.swatches_frame = tk.Frame(root, height = 100, bg = cl.CC_GREY)
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
        self.project_heading = widgets.LabelHeading(self.header_frame, text = "Colour Clipboard")
        self.project_heading.grid(row = 0, column = 0, sticky = "w", pady = 20)

        # Save swatch palette button aligned to the right of the window.
        self.save_button = tk.Button(self.header_frame, bg = cl.CC_WHITE, text = "save")
        self.save_button.grid(row = 0, column = 2)

        # Load swatches palette button aligned to the right of the window.
        self.load_button = tk.Button(self.header_frame, bg = cl.CC_WHITE, text = "load")
        self.load_button.grid(row = 0, column = 3)

        '''
        TAB SECTION

        |[project tab] [project tab] [+]        |
        '''
        # default tab that will be renamed when saved
        self.default_tab_button = widgets.ButtonTab(self.tab_frame, text = "untitied project")
        self.default_tab_button.pack(side = "left", padx = (0, 10))

        # New tab button
        self.tab_button = widgets.ButtonNewTab(self.tab_frame)
        self.tab_button.pack(side = "left", padx = (0, 10))


        '''
        SWATCH SECTION
        '''
        text_swatch = widgets.Swatch(self.swatches_frame, label_text = "TEST", hex_code = "#FF8D28")
        text_swatch.grid(row = 0, column = 0, padx = 5, pady = 5)

        # New swatch button
        self.new_swatch_button = widgets.ButtonNewSwatch(self.swatches_frame, command = self.open_swatch_popup)
        self.new_swatch_button.grid(row = 0, column = 1)


        '''
        FOOTER SECTION
        '''
        footer_text = widgets.LabelFooter(self.footer_frame, text = "Designed & Developed by Kelton Boyter-Grant", bg = cl.CC_WHITE)
        footer_text.pack(padx=20, pady=20, anchor="center")


        '''
        UI FUNCTIONS
        '''

    # Create a new swatch
    def open_swatch_popup(self):
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
                
            print(f"Saving Swatch -> Name: {name_data}, Hex: {hex_data}")
            
            new_swatch = widgets.Swatch(self.swatches_frame, label_text=name_data, hex_code = hex_data)
            new_swatch.grid(column = 0, row = 0, padx = 5, pady = 5)
            
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
        

'''
TKINTER ENTRY POINT
'''
root = tk.Tk()
app = ColourCoperUI(root)
root.mainloop()