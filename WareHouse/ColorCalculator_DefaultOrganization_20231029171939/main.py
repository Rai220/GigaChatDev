'''
Main file for the calculator application. It creates the application window and handles the event loop.
'''
import tkinter as tk
from calculator import Application
def main():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
if __name__ == "__main__":
    main()