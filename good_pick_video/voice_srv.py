import asyncio
import edge_tts
import aiohttp
# TTS功能 txt到MP3
class TextToSpeechConverter:
    def __init__(self, text, output_file, voice="zh-CN-XiaoyiNeural"):
        self.text = text
        self.voice = voice
        self.output_file = output_file.replace(".txt", ".mp3")
        self.webvtt_file = output_file.replace(".txt", ".vtt")


    async def convert_text_to_speech(self, rate="+0%", volume="+0%", timeout=60, retries=3):
        communicate = edge_tts.Communicate(self.text, self.voice, rate=rate, volume=volume)
        submaker = edge_tts.SubMaker()

        attempt = 0
        while attempt < retries:
            try:
                with open(self.output_file, "wb") as file:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            file.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
                print("save: " + self.output_file)
                with open(self.webvtt_file, "w", encoding="utf-8") as file:
                    file.write(submaker.generate_subs())
                print("save: " + self.webvtt_file)
                break
            except aiohttp.ClientTimeout as e:
                attempt += 1
                if attempt == retries:
                    raise e
                print(f"Timeout occurred, retrying {attempt}/{retries}...")
                await asyncio.sleep(2)  # wait a bit before retrying


    def run_conversion(self,rate="+0%", volume="+0%"):
        asyncio.run(self.convert_text_to_speech(rate,volume,60,3))

from pydub import AudioSegment

class MP3Handler:
    def __init__(self, file_path):
        if not file_path.lower().endswith('.mp3'):
            raise ValueError("The file must be an MP3 file.")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        
        self.file_path = file_path
        self.audio = AudioSegment.from_mp3(file_path)

    def get_duration(self):
        """
        Returns the duration of the MP3 file in seconds.
        """
        return len(self.audio) / 1000.0


from moviepy.audio.fx.all import volumex


# ffmpeg实现

import ffmpeg
import subprocess
import os

class MP4ProcessorByffmpeg:
    def __init__(self, mp4_path, gpu = True):
        self.mp4_path = mp4_path
        self.gpu = gpu

    def get_width_height(self):
        # 生成 ffmpeg 命令
        input_video_path = self.mp4_path

        probe_input = ffmpeg.probe(input_video_path)
        input_info = next(stream for stream in probe_input['streams'] if stream['codec_type'] == 'video')
        input_width = int(input_info['width'])
        input_height = int(input_info['height'])
        return input_width, input_height

    
    def crop_video(self, top_pixels, bottom_pixels):
        print(f"Starting crop_video with top_pixels={top_pixels}, bottom_pixels={bottom_pixels}")
        
        # 获取视频的宽度和高度
        probe = ffmpeg.probe(self.mp4_path)
        video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
        width = int(video_info['width'])
        height = int(video_info['height'])

        # 计算新的高度和起始位置
        new_height = height - top_pixels - bottom_pixels
        y_offset = top_pixels

        # 生成 ffmpeg 命令
        input_path = self.mp4_path
        temp_output = append_to_filename(input_path, "_temp")
        # 创建 FFmpeg 命令
        ffmpeg_cmd = (
            ffmpeg
            .input(input_path)
            .crop(x=0, y=y_offset, width=width, height=new_height)
            .output(temp_output, crf='23', r='30', acodec='copy', vcodec='h264_nvenc' if self.gpu else 'libx264')
            .global_args('-map', '0:v', '-map', '0:a')
        )

        # 如果使用GPU，则在命令的最后添加 '-hwaccel nvdec'
        if self.gpu:
            ffmpeg_cmd = ffmpeg_cmd.global_args('-hwaccel', 'nvdec')

        # 打印 ffmpeg 命令行
        cmd_line = ' '.join(ffmpeg_cmd.compile())
        print(f"命令行:  {cmd_line}")

        # 执行 ffmpeg 命令
        ffmpeg_cmd.run()

        print(f"Cropped video saved to {temp_output}")

        replace_file(input_path, temp_output)

    

    def resize_video(self, new_width):
        print(f"Starting resize_video with new_width={new_width}")

        # 获取视频的宽度和高度
        probe = ffmpeg.probe(self.mp4_path)
        video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
        width = int(video_info['width'])
        height = int(video_info['height'])

        # 计算新的高度以保持纵横比
        new_height = int((new_width / width) * height)

        # 生成 ffmpeg 命令
        input_path = self.mp4_path
        temp_output = append_to_filename(input_path, "_temp")
        # 创建 FFmpeg 命令
        ffmpeg_cmd = (
            ffmpeg
            .input(input_path)
            .filter('scale', new_width, new_height)
            .output(temp_output, crf='23',r='30', vcodec='h264_nvenc' if self.gpu else 'libx264', acodec='copy')
        )

        # 如果使用GPU，则在命令的最后添加 '-hwaccel nvdec'
        if self.gpu:
            ffmpeg_cmd = ffmpeg_cmd.global_args('-hwaccel', 'nvdec')

        # 打印 ffmpeg 命令行
        cmd_line = ' '.join(ffmpeg_cmd.compile())
        print(f"命令行:  {cmd_line}")

        # 执行 ffmpeg 命令
        ffmpeg_cmd.run()

        print(f"Resized video saved to {temp_output}")

        replace_file(input_path, temp_output)


    def trim_or_loop_video(self, target_duration):
        print(f"Starting trim_or_loop_video with target_duration={target_duration}")

        # 获取视频的时长
        duration = self.get_video_duration()

        input_path = self.mp4_path
        temp_output = append_to_filename(input_path, "_temp")

        if duration < target_duration:
            # 如果bg视频时长小于目标时长，则循环视频
            loop_count = int(target_duration // duration) + 1
            ffmpeg_cmd = (
                ffmpeg
                .input(input_path, stream_loop=loop_count)
                .output(temp_output, t=target_duration,crf='23',r='30', vcodec='h264_nvenc' if self.gpu else 'libx264')
            )
            # 如果使用GPU，则在命令的最后添加 '-hwaccel nvdec'
            if self.gpu:
                ffmpeg_cmd = ffmpeg_cmd.global_args('-hwaccel', 'nvdec')
        else:
            # 如果视频时长大于目标时长，则截断视频
            ffmpeg_cmd = (
                ffmpeg
                .input(input_path)
                .output(temp_output, t=target_duration,crf='23',r='30', vcodec='copy')
            )

        # 打印 ffmpeg 命令行
        cmd_line = ' '.join(ffmpeg_cmd.compile())
        print(f"命令行:  {cmd_line}")

        # 执行 ffmpeg 命令
        ffmpeg_cmd.run()

        print(f"Trimmed or looped video saved to {temp_output}")

        replace_file(input_path, temp_output)


    def get_video_duration(self):
        print(f"Getting duration for video: {self.mp4_path}")
        probe = ffmpeg.probe(self.mp4_path)
        video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
        duration = float(video_info['duration'])
        print(f"Duration of the video is: {duration} seconds")
        return duration


    def loop_video(self, duration):
        print(f"Starting loop_video with duration={duration}")

        # 获取视频的时长
        probe = ffmpeg.probe(self.mp4_path)
        video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
        video_duration = float(video_info['duration'])

        # 计算需要的循环次数
        loop_count = int(duration // video_duration) + 1

        # 生成 ffmpeg 命令
        input_path = self.mp4_path
        temp_output = append_to_filename(input_path, "_temp")
        ffmpeg_cmd = (
            ffmpeg
            .input(input_path, stream_loop=loop_count)
            .output(temp_output,crf='23',r='30', t=duration)
        )

        # 如果 self.gpu 为 True，则添加硬件加速选项
        if self.gpu:
            ffmpeg_cmd = ffmpeg_cmd.hwaccel('nvdec').output_options('-c:v h264_nvenc')

        # 打印 ffmpeg 命令行
        cmd_line = ' '.join(ffmpeg_cmd.compile())
        print(f"命令行:  {cmd_line}")

        # 执行 ffmpeg 命令
        ffmpeg_cmd.run()

        print(f"Looped video saved to {temp_output}")

        replace_file(input_path,temp_output)


    def overlay_video(self, background_video_path):
        print(f"Starting overlay_video with background_video_path={background_video_path}")

        # 生成 ffmpeg 命令
        input_video_path = self.mp4_path
        temp_output = append_to_filename(input_video_path, "_temp")

        # 获取前景视频和背景视频的信息
        probe_input = ffmpeg.probe(input_video_path)
        input_info = next(stream for stream in probe_input['streams'] if stream['codec_type'] == 'video')
        input_width = int(input_info['width'])
        input_height = int(input_info['height'])

        probe_bg = ffmpeg.probe(background_video_path)
        bg_info = next(stream for stream in probe_bg['streams'] if stream['codec_type'] == 'video')
        bg_width = int(bg_info['width'])
        bg_height = int(bg_info['height'])

        # 计算叠加位置
        overlay_x = (bg_width - input_width) // 2
        overlay_y = (bg_height - input_height) // 2

        # 执行ffmpeg命令进行视频叠加
        ffmpeg_cmd = (
            ffmpeg
            .input(background_video_path)
            .overlay(ffmpeg.input(input_video_path), x=overlay_x, y=overlay_y)
            .output(temp_output, acodec='copy')
        )

        # 如果使用GPU，则在命令的最后添加 '-hwaccel nvdec'
        if self.gpu:
            ffmpeg_cmd = ffmpeg_cmd.global_args('-hwaccel', 'nvdec')

        # 打印 ffmpeg 命令行
        cmd_line = ' '.join(ffmpeg_cmd.compile())
        print(f"命令行:  {cmd_line}")

        # 执行 ffmpeg 命令
        ffmpeg_cmd.run()

        print(f"Cropped video saved to {temp_output}")

        replace_file(input_video_path, temp_output)



    def remove_audio(self):
        print("Removing audio from the video.")
        print(f"Input MP4 file: {self.mp4_path}")
        temp_output = append_to_filename(self.mp4_path, "_temp")

        ffmpeg_cmd = (
            ffmpeg
            .input(self.mp4_path)
            .output(temp_output,crf='23',r='30', vcodec='copy', an=None)
        )

        # 打印 ffmpeg 命令行
        cmd_line = ' '.join(ffmpeg_cmd.compile())
        print(f"命令行:  {cmd_line}")

        # 执行 ffmpeg 命令
        ffmpeg_cmd.run()

        os.replace(temp_output, self.mp4_path)


    def combine_with_mp3(self, mp3_path):
        """
        Add an MP3 audio track to an MP4 video and set its volume.

        Args:
            mp4_path: Path to the input MP4 video file.
            mp3_path: Path to the input MP3 audio file.
            volume: Volume level for the MP3 audio (0.0 to 1.0).
        """

        # Create an output filename with "_audio_added" suffix
        temp_output = append_to_filename(self.mp4_path, "_temp")

        # Build the FFmpeg command
        command = [
            'ffmpeg',
            '-i', self.mp4_path,  # Input MP4 video
            '-i', mp3_path,  # Input MP3 audio
            '-map', '0:v:0',  # Map video stream from the first input
            '-map', '1:a:0',  # Map adjusted audio stream
            '-c:a', 'aac',  # Use AAC for output audio
            '-strict', 'experimental',  # Use experimental AAC encoder if needed
            '-y',  # Overwrite output file
            temp_output,  # Output MP4 file
        ]

        # 如果 self.gpu 为 True，则添加硬件加速选项
        if self.gpu:
            command.extend(['-c:v', 'h264_nvenc', '-hwaccel', 'nvdec'])

        # 添加视频编解码器选项和其他参数
        else:
            command.extend(['-c:v', 'copy'])  # Copy video codec

        # 执行 FFmpeg 命令
        subprocess.run(command)
        # os.replace(temp_output, self.mp4_path)
        replace_file(self.mp4_path, temp_output)


    def insert_image_or_gif(self, img_path, start_time, end_time, position=('center', 'center'), size=None):
        print("Inserting image or GIF into the video.")
        print(f"Input MP4 file: {self.mp4_path}")
        print(f"Input image/GIF file: {img_path}")
        temp_output = append_to_filename(self.mp4_path, "_temp")
        print("temp: "+temp_output)
        ffmpeg_cmd = (
            ffmpeg
            .output(
                ffmpeg.overlay(
                    ffmpeg.input(self.mp4_path),
                    ffmpeg.input(img_path, ss=start_time, t=end_time-start_time, loop=1, reinit_filter=1),
                    x=f'(main_w-overlay_w)/2' if position[0] == 'center' else position[0],
                    y=f'(main_h-overlay_h)/2' if position[1] == 'center' else position[1],
                    enable=f'between(t,{start_time},{end_time})'
                ),
                temp_output
            )
        )

        # 如果 self.gpu 为 True，则添加硬件加速选项
        if self.gpu:
            ffmpeg_cmd = ffmpeg_cmd.output_options('-hwaccel nvdec', '-c:v h264_nvenc')

        # 执行 ffmpeg 命令
        ffmpeg_cmd.run(overwrite_output=True)
        replace_file(self.mp4_path, temp_output)

    def add_subtitles(self, vtt_path, font_size=24, color='white', bgcolor='black', bg_opacity=0.6, position='bottom'):
        print("Adding subtitles to the video.")
        print(f"Input MP4 file: {self.mp4_path}")
        print(f"Input subtitles file: {vtt_path}")
        temp_output = append_to_filename(self.mp4_path, "_temp")
        # 生成 ffmpeg 命令
        ffmpeg_command = [
            'ffmpeg',
            '-i', self.mp4_path,  # 输入视频文件路径
            '-vf', f"subtitles={vtt_path}:force_style='Fontsize={font_size},PrimaryColour={color},BackColour={bgcolor},Alpha={bg_opacity},Alignment={position}'",
            '-c:v', 'libx264',  # 视频编解码器
            '-c:a', 'aac',  # 音频编解码器
            '-y',  # 覆盖输出文件
            temp_output  # 输出视频文件路径，覆盖原有视频文件
        ]

        # 如果 self.gpu 为 True，则添加硬件加速选项
        if self.gpu:
            ffmpeg_command.insert(2, '-hwaccel')
            ffmpeg_command.insert(3, 'nvdec')
            ffmpeg_command.insert(5, '-c:v')
            ffmpeg_command.insert(6, 'h264_nvenc')

        # 执行 ffmpeg 命令
        subprocess.run(ffmpeg_command, overwrite_output=True)
        replace_file(self.mp4_path, temp_output)
        print("Subtitles added to the video.")

    def insert_audio_segment(self, mp3_path, start_time, volume=1.0):
        print("Inserting audio segment into the video.")
        print(f"Input MP4 file: {self.mp4_path}")
        print(f"Input audio MP3 file: {mp3_path}")
        temp_output = append_to_filename(self.mp4_path, "_temp")
        ffmpeg_cmd = (
            ffmpeg
            .input(self.mp4_path)
            .input(mp3_path, ss=0, t=ffmpeg.probe(mp3_path)['format']['duration'])
            .filter('volume', volume)
            .filter('amix', duration='first')
            .output(temp_output)
        )

        # 如果 self.gpu 为 True，则添加硬件加速选项
        if self.gpu:
            ffmpeg_cmd = ffmpeg_cmd.output_options('-c:v h264_nvenc')

        # 打印 ffmpeg 命令行
        cmd_line = ' '.join(ffmpeg_cmd.compile())
        print(f"命令行:  {cmd_line}")

        # 执行 ffmpeg 命令
        ffmpeg_cmd.run(overwrite_output=True)
        replace_file(self.mp4_path, temp_output)

# # 示例用法
# mp4_processor = MP4ProcessorByffmpeg("input.mp4")
# mp4_processor.remove_audio()
# mp4_processor.combine_with_mp3("audio.mp3")
# mp4_processor.insert_image_or_gif("image.gif", start_time=10, end_time=20)
# mp4_processor.add_subtitles("subtitles.vtt")
# mp4_processor.insert_audio_segment("segment.mp3", start_time=30)


def append_to_filename(file_path, append_str):
    # 获取文件路径的目录、文件名和后缀
    directory, filename = os.path.split(file_path)
    name, ext = os.path.splitext(filename)
    
    # 拼接新的文件名
    new_filename = f"{name}{append_str}{ext}"
    
    # 组合成新的文件路径
    new_file_path = os.path.join(directory, new_filename)
    
    return new_file_path


import shutil

def copy_file(source_file_path, destination_file_path):
    """
    复制文件并指定新文件的名字

    参数:
    source_file_path (str): 原始文件的路径
    destination_file_path (str): 目标文件的路径（包括新的文件名）

    返回:
    None
    """
    try:
        shutil.copy(source_file_path, destination_file_path)
        print(f"文件已成功复制到 {destination_file_path}")
    except Exception as e:
        print(f"复制文件时出错: {e}")

# # 示例用法
# source = "path/to/source/file.txt"
# destination = "path/to/destination/newfile.txt"
# copy_file(source, destination)


import os

def replace_file(source_path, target_path):
    """
    Delete the source file and rename the target file to the source file's name.

    Args:
        source_path (str): Path to the source file to be deleted.
        target_path (str): Path to the target file to be renamed.
    """
    try:
        # Delete the source file
        if os.path.exists(source_path):
            os.remove(source_path)
            print(f"Deleted source file: {source_path}")
        else:
            print(f"Source file not found: {source_path}")

        # Rename the target file to the source file's name
        os.rename(target_path, source_path)
        print(f"Renamed target file {target_path} to {source_path}")

    except OSError as e:
        print(f"Error occurred: {e}")

