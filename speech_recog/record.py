"""PyAudio example: Record a few seconds of audio and save to a WAVE file."""

import numpy
import scipy.signal


def record(channels, format, rate, seconds, plot=False):

    import pyaudio
    import wave
    import matplotlib.pyplot as plt

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = seconds

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    numpyframes = numpy.array(frames)

    decoded = numpy.fromstring(numpyframes, 'int16')
    filtered = butter_bandpass_filter(decoded, lowcut = 200.0, highcut = 6500.0, fs = RATE, order=5)
    filtered = numpy.array(filtered, 'int16')

    threshold = 2000
    new_start = find_silence_end(filtered, threshold=threshold)
    new_end = find_silence_end(filtered, threshold=threshold, forwards=False)

    filtered = filtered[new_start : new_end]
    decoded = decoded[new_start : new_end]

    filtered_str = filtered.tostring()

    x = list(range(0, decoded.size))

    if (plot):
        plt.figure(1)
        plt.clf()
        plt.plot(x, decoded, label="Noisy signal")
        plt.plot(x, filtered, label="Filtered signal")
        plt.xlabel("Sample #")
        plt.legend(loc="upper right")

        plt.show()

    return filtered_str

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = scipy.signal.butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = scipy.signal.filtfilt(b, a, data)
    return y

def save_wave(data, filename, nchannels, format, rate):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(nchannels)
    wf.setsampwidth(format)
    wf.setframerate(rate)
    wf.writeframes(data)#b''.join(frames))
    wf.close()

def load_file(filename):

    import wave

    spf = wave.open(filename, 'r')
    x = spf.readframes(-1)
    x = numpy.fromstring(x, 'Int16')
    rate = spf.getframerate()

    return x, rate

def get_formants(data, rate):

    from audiolazy import lpc
    import math

    # Get Hamming window.
    N = len(data)
    w = numpy.hamming(N)

    # Apply window and high pass filter.
    x1 = data * w
    x1 = scipy.signal.lfilter([1], [1., 0.63], x1)

    # Get LPC.
    ncoeff = int(2 + rate / 1000)
    filt = lpc(x1, ncoeff)

    # Get roots.
    rts = numpy.roots(filt.numerator)
    rts = [r for r in rts if numpy.imag(r) >= 0]

    # Get angles.
    angz = numpy.arctan2(numpy.imag(rts), numpy.real(rts))

    # Get frequencies.
    frqs = sorted(angz * (rate / (2 * math.pi)))

    return frqs 

def find_silence_end(data, threshold=1000, forwards=True):

    window_size = 5
    if (len(data) <= window_size):
        return data

    signal = data

    if not forwards:
        signal = list(reversed(data))

    abs_signal = numpy.abs(signal)

    for i in range(0, len(abs_signal)):

        if abs_signal[i] > threshold:
            index = i
            if not forwards:
                index = len(abs_signal) - i
            return index

    return data

def find_extrema(data, maximum=True):

    data = numpy.abs(data)
    widths = numpy.arange(1000, 6000, 500)
    peakind = scipy.signal.find_peaks_cwt(data, widths)

    return peakind

if __name__ == "__main__":

    import sys
    import pyaudio

    CHANNELS = 1
    FORMAT = pyaudio.pyInt16
    RATE = 44100
    SECONDS = sys.argv[1]
    WAVE_OUTPUT_FILENAME = sys.argv[2]

    audio = record(CHANNELS, FORMAT, RATE, SECONDS, plot=True)

    save_wave(audio, WAVE_OUTPUT_FILENAME, CHANNELS, p.get_sample_size(FORMAT), RATE)
