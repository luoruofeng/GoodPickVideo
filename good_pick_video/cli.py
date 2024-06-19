import sys
import threading
import time
from good_pick_video.voice_srv import MP3Handler, TextToSpeechConverter, MP4ProcessorByffmpeg, copy_file, append_to_filename
from good_pick_video.config import Config
from good_pick_video.subtitle import SubtitleConverter
from good_pick_video.subtitle import extract_and_remove 
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
        txt_file = os.path.join(file_path, last_folder_name(file_path)+".txt")
        mp4_file = txt_file.replace(".txt", ".mp4")
        mp3_file = txt_file.replace(".txt", ".mp3")
        vtt_file = txt_file.replace(".txt", ".vtt")
        ass_file = txt_file.replace(".txt", ".ass")
        
        if txt_file == None:
            print("没有在文件夹下找到txt文件: "+file_path)
            return
        
        txt = read_txt_file(txt_file)
        single_star_words, double_star_words, txt = extract_and_remove(txt) #去除 * **  找出被* **围绕的词
        print(f"单星号词:{single_star_words}")
        print(f"双星号词:{double_star_words}")
        print(f"无星号内容:{txt}")
        

        if not os.path.exists(mp3_file): #txt创建mp3
            text2speech_converter = TextToSpeechConverter(txt, txt_file, Config().voice_cli["voice"])
            text2speech_converter.run_conversion(Config().voice_cli["rate"],Config().voice_cli["volume"])
        mp3handler = MP3Handler(mp3_file)
        music_duration = mp3handler.get_duration() # mp3时长

        processor = MP4ProcessorByffmpeg(mp4_file, gpu=True)
        if not os.path.exists(mp4_file): #生成纯色的mp4
            print("视频文件不存在 生成新的纯色mp4",mp4_file)
            processor.generate_blank_video(width=Config().video_cli["width"], height=Config().video_cli["height"], color=Config().video_cli["bg_color"], duration=music_duration)
        
        
        video_duration = processor.get_video_duration() #mp4时长
        if music_duration > video_duration:
            print(f'声音时长于视频时长: 声音{mp3_file}文件 视频{mp4_file}文件 声音{music_duration}秒 视频{video_duration}秒')
            return
        processor.crop_video(Config().voice_cli["top_padding"], Config().voice_cli["bottom_padding"]) #mp4裁剪大小
        
        #bg视频
        if Config().voice_cli["bg_path"] is not None:
            bg_width = 0
            bg_file = append_to_filename(mp4_file,"_bg")
            if not os.path.exists(bg_file):
                copy_file(os.path.join(CURRENT_DIR,Config().voice_cli["bg_path"]), bg_file) #复制bg视频
            bg_processor = MP4ProcessorByffmpeg(bg_file)
            bg_width,_ = bg_processor.get_width_height()
            bg_processor.trim_or_loop_video(video_duration) #bg视频长度 = 视频长度
            processor.resize_video(bg_width) #修改视频的比例 根据bg视频的宽度
            processor.overlay_video(bg_file) #将视频重叠放到bg视频上
        
        # 字幕
        formatted_vtt_file = append_to_filename(vtt_file,"_formatted")
        splited_vtt_file = append_to_filename(vtt_file,"_split")
        if vtt_file != None:
            if Config().subtitle_cli["keyword_dict_path"] is not None:#重新分词字幕文件
                text2speech_converter = SubtitleConverter(vtt_file,segmenter_path=os.path.join(CURRENT_DIR,Config().subtitle_cli["keyword_dict_path"]),single_star_words = single_star_words, double_star_words = double_star_words)
            else:#无需分词字幕文件
                text2speech_converter = SubtitleConverter(vtt_file,single_star_words = single_star_words, double_star_words = double_star_words)
            
            text2speech_converter.fontname = Config().subtitle_cli["font_family"]
            text2speech_converter.fontsize = Config().subtitle_cli["font_size"]
            text2speech_converter.primary_colour = Config().subtitle_cli["font_color"]


            text2speech_converter.format_vtt_file(formatted_vtt_file)
            if Config().subtitle_cli["split"] is True:
                text2speech_converter.split_vtt(splited_vtt_file)#分词显示每行字幕
            print("-----------------------------------")
            text2speech_converter.convert_vtt_to_ass(ass_file)
            processor.add_ass_subtitles(ass_file)

        processor.remove_audio() # 静音
        processor.combine_with_mp3(mp3_file) # mp4添加配音

    
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