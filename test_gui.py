#!/usr/bin/env python3
"""
Simple test GUI to debug the white screen issue
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys

def test_gui():
    print("Creating test GUI...")
    
    root = tk.Tk()
    root.title("ZeroTrace Test GUI")
    root.geometry("800x600")
    root.configure(bg='#0f1419')
    
    # Test label
    label = tk.Label(root, text="ZeroTrace Pro Test", 
                    font=('Segoe UI', 24, 'bold'),
                    bg='#0f1419', fg='#f0f6fc')
    label.pack(pady=50)
    
    # Test button
    button = tk.Button(root, text="Test Button",
                      font=('Segoe UI', 12),
                      bg='#58a6ff', fg='#f0f6fc',
                      command=lambda: messagebox.showinfo("Test", "Button works!"))
    button.pack(pady=20)
    
    print("Starting mainloop...")
    root.mainloop()

if __name__ == "__main__":
    test_gui()
