from tkinter import *
import pyaudio
import record
import fnmatch
import os
import numpy

class App:

    # Recording constants
    CHANNELS = 1
    FORMAT = pyaudio.paInt16
    RATE = 44100
    SECONDS = 2

    # Vocabulary
    VOCABULARY = [
        'hello',
        'do',
        'delete',
        'edit',
        'exit',
        'paste',
        'put',
        'bye',
        'backup',
        'list'
    ]

    def __init__(self, master):

        frame = Frame(master)
        frame.pack()

        # Initialize quit button
        self.button = Button(
            frame, text="QUIT", fg="red", command=frame.quit
            )
        self.button.pack(side=LEFT)

        # Initialize record button
        self.record = Button(frame, text="Record", state=DISABLED, command=self.record)
        self.record.pack(side=LEFT)

        # Initialize label
        self.recordtext = StringVar()

        self.recording = Label(master, textvariable=self.recordtext)
        self.recording.pack()

    def init_model(self):

        self.recordtext.set("Initializing")
        self.recording.update()

        # for each word in dictionary, call __get_word_model__
        self.model = {}
        for word in App.VOCABULARY:
            self.model[word] = self.__get_formant_model__(word)
            print(self.model[word])

        self.record.config(state=NORMAL)
        self.recordtext.set("")

    def record(self):

        signal = record.record(App.CHANNELS,
            App.FORMAT,
            App.RATE,
            App.SECONDS,
            update_text_callback=self.set_text)

        self.set_text("Processing")
        word = self.process(signal)

        self.set_text("You said: {:s}".format(word))

    def process(self, signal):

        # compute formant of signal
        formant = numpy.array(record.get_formants(signal, App.RATE))

        # get minimum formant length and scale so that we can match them
        # for each word in vocab, get average standard deviation of formants
        min_std = float('inf')
        min_word = None
        print(formant[0:5])
        for word, model in self.model.items():
            mi = min(len(formant), len(model))
            formant = formant[0:mi]
            model = model[0:mi]

            ave_std = numpy.mean(numpy.abs(numpy.diff((formant, model), axis=0)))
            if min_std > ave_std:
                min_std = ave_std
                min_word = word

        # word is one with smallest average standard deviation
        return min_word

    def set_text(self, text):
        self.recordtext.set(text)
        self.recording.update()

    def __get_word_model__(self, word):

        print("initializing model for word {:s}".format(word))

        # find files associated with word and load their data
        files = []
        for file in os.listdir(word):
            if fnmatch.fnmatch(file, word + '*.wav'):
                dat, rate = record.load_file(word + '\\' + file)
                files.append(dat)

        model = {}

        # get formants
        model['formants'] = self.__get_formant_model__(files)

        # get length in seconds
        model['length'] = self.__get_length_model__(files)

        # get # zero crossings



    def __get_formant_model__(self, files, num_formants=5):

        # compute formants for each of them
        formants = []
        for data in files:
            formant = numpy.array(record.get_formants(data, App.RATE))
            formants.append(formant[0:num_formants])

        # adjust formant counts so they are all the same
        min_formant_count = min([len(f) for f in formants])
        for i in range(len(formants)):
            if len(formants[i] > min_formant_count):
                formants[i] = formants[i][0:min_formant_count]

        # get average formants across whole set
        form_ave = numpy.median(formants, axis=0)

        # return this as a model
        return form_ave

    def __get_length_model__(self, files):

        lengths = [(len(f) / App.RATE) for f in files]

        # get median file length in seconds
        med = numpy.median(lengths)
        return med

    def __get_zero_crossings__(self, files):

        # get # crossings for each file
        crossings = []
        for data in files:

            count = 0
            prev_val = None
            for datum in data:
                if prev_val is None:
                    prev_val = datum
                    continue
                if datum == 0:
                    continue
                else if prev_val ^ datum < 0:
                    count += 1

                prev_val = datum





root = Tk()

app = App(root)
root.after(100, app.init_model)

root.mainloop()
root.destroy() # optional; see description below