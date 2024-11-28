import tkinter as tk
from tkinter import messagebox

def show_message():
    messagebox.showinfo("Information", "Hello, macOS!")

app = tk.Tk()
app.title("Hello macOS App")
app.geometry("300x200")

button = tk.Button(app, text="Click Me", command=show_message)
button.pack(expand=True)

app.mainloop()
