'''
This is the main file of the pixel drawing application.
'''
from tkinter import Tk, Canvas, Button, filedialog
class PixelDrawingApp:
    def __init__(self, root):
        self.root = root
        self.canvas = Canvas(self.root, width=500, height=500, bg='white')
        self.canvas.pack()
        self.canvas.bind('<B1-Motion>', self.draw_pixel)
        self.save_button = Button(self.root, text='Save', command=self.save_canvas)
        self.save_button.pack()
    def draw_pixel(self, event):
        x = event.x
        y = event.y
        self.canvas.create_rectangle(x, y, x+1, y+1, fill='black')
    def save_canvas(self):
        file_path = filedialog.asksaveasfilename(defaultextension='.png')
        if file_path:
            self.canvas.postscript(file=file_path, colormode='color')
            self.root.update()
            print(f'Canvas saved as {file_path}')
if __name__ == '__main__':
    root = Tk()
    app = PixelDrawingApp(root)
    root.mainloop()