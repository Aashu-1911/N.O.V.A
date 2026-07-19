import pyttsx3

for i in range(5):
    engine = pyttsx3.init()     # NEW engine every iteration
    print("Speaking", i)
    engine.say(f"This is message {i}")
    engine.runAndWait()
    engine.stop()