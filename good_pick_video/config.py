import yaml
import sys

# usage： Config().music_cli["task"]

CNF = None

class Config:
    def __init__(self, path=None):
        global CNF
        if CNF == None:
            if path == None:
                print("The configuration file must be obtained")
                sys.exit(1)
            CNF = self.load_config(path)

    def load_config(self,path):
        with open(path, 'r') as stream:
            try:
                config = yaml.safe_load(stream)
                return config
            except yaml.YAMLError as e:
                print(e)
                return None

    @property
    def music_cli(self):
        return CNF['music_cli']
    
    @property
    def voice_cli(self):
        return CNF['voice_cli']
    
    @property
    def video_cli(self):
        return CNF['video_cli']
    
    @property
    def subtitle_cli(self):
        return CNF['subtitle_cli']
