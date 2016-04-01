from tkinter import *
import pyaudio
import record
import fnmatch
import os
import numpy
import operator

class App:

    # Recording constants
    CHANNELS = 1
    FORMAT = pyaudio.paInt16
    RATE = 44100
    SECONDS = 2

    # Model constants
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
    FORMANTS_KEY = 'formants'
    LENGTH_KEY = 'length'
    ZCROSSINGS_KEY = 'zero_crossings'

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

        # for each word in dictionary, call __get_model__
        self.model = {}
        for word in App.VOCABULARY:

            print("initializing model for word {:s}".format(word))

            # find files associated with word and load their data
            signals = []
            for file in os.listdir(word):
                if fnmatch.fnmatch(file, word + '*.wav'):
                    dat, rate = record.load_file(word + '\\' + file)
                    signals.append(dat)

            self.model[word] = self.__get_model__(signals)
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

        signal = [signal]

        # compute model for signal
        input_model = self.__get_model__(signal)
        print(input_model)
        #formant = numpy.array(record.get_formants(signal, App.RATE))

        # compare formants
        form_weights = self.__compare_formants__(input_model[App.FORMANTS_KEY])

        # compare lengths
        len_weights = self.__compare_lengths__(input_model[App.LENGTH_KEY])

        # compare zero crossings
        zcross_weights = self.__compare_zero_crossings__(input_model[App.ZCROSSINGS_KEY])

        # sum weights together and pick item with most weight
        sums = {}
        for word in self.model:
            sums[word] = form_weights[word] + len_weights[word] + zcross_weights[word]

        print('formants', form_weights)
        print('length', len_weights)
        print('zcrossings', zcross_weights)

        max_word = max(sums.items(), key=operator.itemgetter(1))[0]
        return max_word

    def set_text(self, text):
        self.recordtext.set(text)
        self.recording.update()

    def __get_model__(self, signals):

        model = {}

        # get formants
        model[App.FORMANTS_KEY] = self.__get_formant_model__(signals)

        # get length in seconds
        model[App.LENGTH_KEY] = self.__get_length_model__(signals)

        # get # zero crossings
        model[App.ZCROSSINGS_KEY] = self.__get_zero_crossings__(signals)

        return model

    def __get_formant_model__(self, signals, num_formants=5):

        # compute formants for each of them
        formants = []
        for data in signals:
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

    def __get_length_model__(self, signals):

        # get length of each file in seconds
        lengths = [(len(f) / App.RATE) for f in signals]

        # get median file length in seconds
        med = numpy.median(lengths)
        return med

    def __get_zero_crossings__(self, signals):

        # get # zero crossings for each file
        crossings = []
        for data in signals:
            crossings.append(len(numpy.where(numpy.diff(numpy.signbit(data)))[0]))

        med_crossings = numpy.median(crossings)
        return med_crossings

    def __compare_formants__(self, input_formants):

        # get minimum formant length and scale so that we can match them
        # for each word in vocab, get average absolute difference of formants
        diffs = {}
        print(input_formants[0:5])
        for word, model in self.model.items():
            model_formants = model[App.FORMANTS_KEY]

            mi = min(len(input_formants), len(model_formants))
            input_formants = input_formants[0:mi]
            model_formants = model_formants[0:mi]

            diffs[word] = numpy.mean(numpy.abs(numpy.diff((input_formants, model_formants), axis=0)))

        weights = self.__reverse_normalize__(diffs)
        return weights

    def __compare_lengths__(self, input_length):

        # get absolute difference of lengths between input and all words
        length_diffs = {}
        for word, model in self.model.items():
            model_length = model[App.LENGTH_KEY]
            length_diffs[word] = numpy.abs(model_length - input_length)

        weights = self.__reverse_normalize__(length_diffs)
        return weights

    def __compare_zero_crossings__(self, input_zcrossing_count):

        # get absolute difference of number of zero crossings between input and all words
        zcrossings_diffs = {}
        for word, model in self.model.items():
            model_zcrossing_count = model[App.ZCROSSINGS_KEY]
            zcrossings_diffs[word] = numpy.abs(model_zcrossing_count - input_zcrossing_count)

        weights = self.__reverse_normalize__(zcrossings_diffs)
        return weights

    def __reverse_normalize__(self, value_dict):

        # calculate [0, 1] normalized values across keys
        # lower difference means more higher value (reversed)
        max_val = max(value_dict.items(), key=operator.itemgetter(1))[1]
        min_val = min(value_dict.items(), key=operator.itemgetter(1))[1]
        normalized = {key: 1.0 - self.__normalize__(val, max_val, min_val)
            for (key, val)
            in value_dict.items()
        }

        return normalized

    def __normalize__(self, value, max_val, min_val):

        if (max_val - min_val == 0.0):
            return 1.0
        return (value - min_val) / (max_val - min_val)

root = Tk()

app = App(root)
root.after(100, app.init_model)

root.mainloop()
root.destroy() # optional; see description below