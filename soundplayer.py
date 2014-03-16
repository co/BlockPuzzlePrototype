import soundplay, threading, time


SOUND_THREADS = 5


class SoundThread( threading.Thread ):
    def __init__(self):
        self.next_sound = None
        super(SoundThread, self).__init__()

    def run(self):
        while True:
            while(self.next_sound == None):
                time.sleep(0) #yield
            soundplay.playsound(self.next_sound)
            self.next_sound = None


class SoundPlayer(object):
    def __init__(self):
        self.threads = []
        self.next_thread = 0
        for _ in range(SOUND_THREADS):
            sound_thread = SoundThread()
            sound_thread.daemon = True
            sound_thread.start()
            self.threads.append(sound_thread)

    def play_sound(self, sound_file):
        self.threads[self.next_thread].next_sound = sound_file
        self.next_thread = (self.next_thread + 1) % SOUND_THREADS
        print self.next_thread
