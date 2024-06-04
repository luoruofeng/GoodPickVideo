import sys
import threading
import time
from good_pick_video.voice_srv import MP3Handler, TextToSpeechConverter, MP4ProcessorByffmpeg, copy_file, append_to_filename
from good_pick_video.config import Config
from good_pick_video.subtitle import SubtitleConverter
import os
from argparse import ArgumentParser
import signal
from good_pick_video.util import *

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(CURRENT_DIR,'config/config.yml')


def _get_args():
    parser = ArgumentParser()
    parser.add_argument( "-c", "--config-path", type=str, default=DEFAULT_CONFIG_PATH,
                        help="config yaml file path, default to %(default)r")
    parser.add_argument( "-i", "--input-dir", type=str, default=None,required=True, 
                        help="操作文件夹")
    args = parser.parse_args()
    return args


SHUT_DOWN_EVENT = threading.Event()
SHUTDOWN_SIGNAL_RECEIVED = False # 设置一个标志，初始时为 False

def signal_handler(sig, frame):
    print("SHUT DOWN!")
    global SHUTDOWN_SIGNAL_RECEIVED
    # 检查标志是否已经被设置
    if SHUTDOWN_SIGNAL_RECEIVED:
        # 如果已经接收到信号，直接返回
        return
    # 设置标志，表示信号已经接收
    SHUTDOWN_SIGNAL_RECEIVED = True
    SHUT_DOWN_EVENT.set()
    print("good bye!")
    sys.exit(0)


def main():
    threads = []

    args = _get_args() # set launch arguments
    Config(DEFAULT_CONFIG_PATH) # load config yaml
    signal.signal(signal.SIGINT, signal_handler)  # 注册Ctrl+C信号处理程序

    # 创造背景音乐
    # manager = MusicManager(Config().music_cli["task"],Config().music_cli["model"])
    # music_t = threading.Thread(target=manager.generate_music, args=(args.description, args.output_file, SHUT_DOWN_EVENT, args.num_musics))
    # music_t.start()
    # threads.append(music_t)

    def handler(file_path):
        txt_file = find_file_with_extension(file_path, "txt")
        mp4_file = find_file_with_extension(file_path, "mp4")
        if txt_file == None:
            print("没有在文件夹下找到txt文件: "+file_path)
            return
        mp3_file = txt_file.replace(".txt", ".mp3")
        vvt_file = txt_file.replace(".txt", ".vvt")
        if txt_file != None and mp4_file != None: 
            if not os.path.exists(mp3_file): #txt创建mp3
                txt = read_txt_file(txt_file)
                converter = TextToSpeechConverter(txt, txt_file, Config().voice_cli["voice"])
                converter.run_conversion(Config().voice_cli["rate"],Config().voice_cli["volume"])
            # mp3handler = MP3Handler(mp3_file)
            # music_duration = mp3handler.get_duration() # mp3时长
            # processor = MP4ProcessorByffmpeg(mp4_file, gpu=True)
            # video_duration = processor.get_video_duration() #mp4时长
            # if music_duration > video_duration:
            #     print(f'声音时长于视频时长: 声音{mp3_file}文件 视频{mp4_file}文件 声音{music_duration}秒 视频{video_duration}秒')
            #     return
            # processor.remove_audio() # 静音
            # processor.combine_with_mp3(mp3_file) # mp4添加配音
            # processor.crop_video(Config().voice_cli["top_padding"], Config().voice_cli["bottom_padding"]) #mp4裁剪大小

            # #bg视频
            # if Config().voice_cli["bg_path"] is not None:
            #     bg_width = 0
            #     bg_file = append_to_filename(mp4_file,"_bg")
            #     if not os.path.exists(bg_file):
            #         copy_file(os.path.join(CURRENT_DIR,Config().voice_cli["bg_path"]), bg_file) #复制bg视频
            #     bg_processor = MP4ProcessorByffmpeg(bg_file)
            #     bg_width,_ = bg_processor.get_width_height()
            #     bg_processor.trim_or_loop_video(video_duration) #bg视频长度 = 视频长度
            #     processor.resize_video(bg_width) #修改视频的比例 根据bg视频的宽度
            #     processor.overlay_video(bg_file) #将视频重叠放到bg视频上
            
            # 字幕
            vtt_file = txt_file.replace(".txt", ".vtt")
            ass_file = txt_file.replace(".txt", ".ass")
            formatted_vtt_file = append_to_filename(vtt_file,"_formatted")
            if vtt_file != None:
                converter = SubtitleConverter(vtt_file)
                converter.format_vtt_file(formatted_vtt_file)
                converter.convert_vtt_to_ass(ass_file)
    
    organizer = FileOrganizer(args.input_dir)
    organizer.process_subdirectories(handler)
    # manager = TextToSpeechConverter()
    # music_t = threading.Thread(target=manager.generate_music, args=(args.description, args.output_file, SHUT_DOWN_EVENT, args.num_musics))
    # music_t.start()
    # threads.append(music_t)
    
    while True:
        try:
            time.sleep(1000)  # 模拟程序持续运行中
        except KeyboardInterrupt:
            # 如果发生 KeyboardInterrupt，例如在 time.sleep() 中按下了 Ctrl+C
            print('\n发生 KeyboardInterrupt，程序继续运行...')
            break
    print("DDDDDON")
    for t in threads:
        t.join()

    print("Done!")


if __name__ == "__main__":
    main()