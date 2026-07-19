import pyttsx3
import time

engine = pyttsx3.init()

# Try a different voice
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[2].id)  # Zira

engine.setProperty("rate", 170)

for i in range(5):
    print(f"Speaking {i}")
    engine.say(f"This is message {i}")
    engine.runAndWait()
    print("Finished")
    time.sleep(1)

print("Done")