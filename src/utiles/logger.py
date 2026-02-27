import datetime

def log(message):
    heure = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{heure}] {message}")