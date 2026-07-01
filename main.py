'''
The main UI for colour clipboard using tkinter as the graphical layer.
'''

import tkinter as tk
from tkinter import ttk
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
        self.tab_frame = tk.Frame(root, height = 50, bg = cl.CC_BLACK)
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
        # New tab button
        self.tab_button = widgets.ButtonNewTab(self.tab_frame)
        self.tab_button.pack(side = "left", padx = (0, 10))


        '''
        SWATCH SECTION
        '''


        '''
        FOOTER SECTION
        '''
        footer_text = widgets.LabelFooter(self.footer_frame, text = "Designed & Developed by Kelton Boyter-Grant", bg = cl.CC_WHITE)
        footer_text.pack(padx=20, pady=20, anchor="center")


        '''
        UI FUNCTIONS
        '''
        

'''
TKINTER ENTRY POINT
'''
root = tk.Tk()
app = ColourCoperUI(root)
root.mainloop()