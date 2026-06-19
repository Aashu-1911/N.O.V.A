from pycaw.pycaw import AudioUtilities

devices = AudioUtilities.GetSpeakers()

print(type(devices))
print(dir(devices))