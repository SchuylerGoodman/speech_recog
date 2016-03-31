from tkinter import *

class App:

    def __init__(self, master):

        frame = Frame(master)
        frame.pack()

        self.button = Button(
            frame, text="QUIT", fg="red", command=frame.quit
            )
        self.button.pack(side=LEFT)

        self.record = Button(frame, text="Record", command=self.record)
        self.record.pack(side=LEFT)

        self.recordtext = StringVar()
        self.recording = Label(master, textvariable=self.recordtext)
        self.recording.pack()

    def record(self):
        self.recordtext.set("Recording")

root = Tk()

app = App(root)

root.mainloop()
root.destroy() # optional; see description below