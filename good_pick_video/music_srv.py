from transformers import pipeline
import scipy.io.wavfile as wavfile
import os

def get_absolute_music_path(file_name):
    # 获取当前脚本所在的目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接文件夹路径和文件名
    music_dir = os.path.join(script_dir, "music")
    file_path = os.path.join(music_dir, file_name)
    # 返回文件的绝对路径
    return os.path.abspath(file_path)


import torch
class MusicManager:
    def __init__(self,task="text-to-audio" , model="facebook/musicgen-small"):
        if torch.cuda.is_available():
            print("使用cuda")
            device = 'cuda'
        else:
            print("使用cpu")
            device = "cpu"
        self.synthesiser = pipeline(task, model, device=device)
    
    def generate_music(self, description, output_file, stop_event, num_tracks=1):
        for track_num in range(num_tracks):
            if not stop_event.is_set():
                music = self.synthesiser(description, forward_params={"do_sample": True})
                track_file = get_absolute_music_path((output_file+"{}.wav").format(track_num))
                wavfile.write(track_file, rate=music["sampling_rate"], data=music["audio"])
                print("save to " + track_file)
            else:
                print("music manager have done!")
                break