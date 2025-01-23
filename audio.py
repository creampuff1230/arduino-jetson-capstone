import pyaudio
import numpy as np
import speech_recognition as sr
from scipy.signal import find_peaks

# Constants
SAMPLE_RATE = 44100  # Audio sample rate
CHUNK = 1024  # Number of samples per frame
TONE_THRESHOLD = 1000  # Amplitude threshold to detect tones
FREQUENCY_BOUNDS = (500, 2000)  # Frequency range for the tone (Hz)

def recognize_speech(audio_data):
    """Recognize spoken words using SpeechRecognition."""
    recognizer = sr.Recognizer()
    try:
        text = recognizer.recognize_google(audio_data)
        print(f"Recognized speech: {text}")
        if "left" in text.lower():
            return 0  # Left
        elif "right" in text.lower():
            return 1  # Right
    except sr.UnknownValueError:
        print("Could not understand audio.")
    return None  # No recognizable word

def detect_tone_direction(audio_frames):
    """Detect tone and locate its direction."""
    left_channel = audio_frames[::2]  # Assuming stereo, left channel is every 2nd sample
    right_channel = audio_frames[1::2]  # Right channel is every other 2nd sample

    # Convert to frequency domain
    fft_left = np.fft.rfft(left_channel)
    fft_right = np.fft.rfft(right_channel)

    # Get the frequencies and corresponding amplitudes
    freqs = np.fft.rfftfreq(len(left_channel), d=1/SAMPLE_RATE)
    left_amplitude = np.abs(fft_left)
    right_amplitude = np.abs(fft_right)

    # Detect peaks in the frequency range of interest
    peak_indices_left = find_peaks(left_amplitude, height=TONE_THRESHOLD)[0]
    peak_indices_right = find_peaks(right_amplitude, height=TONE_THRESHOLD)[0]

    # Filter peaks within frequency bounds
    tone_detected_left = any(FREQUENCY_BOUNDS[0] <= freqs[i] <= FREQUENCY_BOUNDS[1] for i in peak_indices_left)
    tone_detected_right = any(FREQUENCY_BOUNDS[0] <= freqs[i] <= FREQUENCY_BOUNDS[1] for i in peak_indices_right)

    if tone_detected_left and not tone_detected_right:
        return 0  # Tone on the left
    elif tone_detected_right and not tone_detected_left:
        return 1  # Tone on the right
    else:
        return None  # No clear tone detected

def process_audio():
    """Main function to record audio and detect speech or tones."""
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source)

        print("Listening for audio...")
        audio = recognizer.listen(source, timeout=5)  # Record for up to 5 seconds

    # Process the speech part
    speech_result = recognize_speech(audio)
    if speech_result is not None:
        return speech_result

    # Process the tone part
    # Note: Here, we assume raw audio frames are accessible (via a different library if needed)
    print("No speech recognized. Checking for tones...")
    with mic as source:
        pyaudio_instance = pyaudio.PyAudio()
        stream = pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=2,  # Stereo
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        audio_frames = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
        stream.close()

    return detect_tone_direction(audio_frames)

if __name__ == "__main__":
    direction = process_audio()
    if direction == 0:
        print("Detected: Left")
    elif direction == 1:
        print("Detected: Right")
    else:
        print("No clear detection.")
