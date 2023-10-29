'''
This file contains the definitions of the Application and Button classes, as well as the calculate function.
'''
import tkinter as tk
import ast
import operator as op
# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.USub: op.neg}
def evaluate_expr(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](evaluate_expr(node.left), evaluate_expr(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](evaluate_expr(node.operand))
    else:
        raise TypeError(node)
def calculate(expression):
    try:
        return evaluate_expr(ast.parse(expression, mode='eval').body)
    except Exception as e:
        return str(e)
class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid()
        self.create_widgets()
    def create_widgets(self):
        self.entry = tk.Entry(self)
        self.entry.grid(row=0, column=0, columnspan=4)
        colors = ['red', 'green', 'blue', 'yellow']
        for i in range(9):
            Button(self, text=str(i+1), color=colors[i%4], command=lambda i=i: self.entry.insert(tk.END, str(i+1))).grid(row=1+i//3, column=i%3)
        Button(self, text='0', color=colors[3], command=lambda: self.entry.insert(tk.END, '0')).grid(row=4, column=0)
        Button(self, text='.', color=colors[2], command=lambda: self.entry.insert(tk.END, '.')).grid(row=4, column=1)
        Button(self, text='=', color=colors[1], command=self.calculate).grid(row=4, column=2)
        Button(self, text='+', color=colors[0], command=lambda: self.entry.insert(tk.END, '+')).grid(row=1, column=3)
        Button(self, text='-', color=colors[1], command=lambda: self.entry.insert(tk.END, '-')).grid(row=2, column=3)
        Button(self, text='*', color=colors[2], command=lambda: self.entry.insert(tk.END, '*')).grid(row=3, column=3)
        Button(self, text='/', color=colors[3], command=lambda: self.entry.insert(tk.END, '/')).grid(row=4, column=3)
    def calculate(self):
        try:
            result = globals()['calculate'](self.entry.get())
            self.entry.delete(0, tk.END)
            self.entry.insert(tk.END, str(result))
        except Exception:
            self.entry.delete(0, tk.END)
            self.entry.insert(tk.END, "Ошибка в выражении")
class Button(tk.Button):
    def __init__(self, master=None, text=None, color=None, command=None):
        super().__init__(master, text=text, bg=color, fg=color, command=command)
        self.grid()