import webvtt
import re
from good_pick_video.segment_srv import Segmenter
from good_pick_video import util
from datetime import timedelta
from good_pick_video.config import Config

class SubtitleConverter:
    def __init__(self, vtt_path, name="Default", fontname="Arial", fontsize=20, primary_colour="&H00FFFFFF", secondary_colour="&H000000FF", outline_colour="&H00000000", back_colour="&H64000000", bold=-1, italic=0, underline=0, strikeout=0, scale_x=100, scale_y=100, spacing=0, angle=0, border_style=1, outline=1, shadow=0, alignment=4, margin_l=10, margin_r=10, margin_v=10, encoding=1, segmenter_path = None):
        self.vtt_path = vtt_path
        self.name = name
        self.fontname = fontname
        self.fontsize = fontsize
        self.primary_colour = primary_colour
        self.secondary_colour = secondary_colour
        self.outline_colour = outline_colour
        self.back_colour = back_colour
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strikeout = strikeout
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.spacing = spacing
        self.angle = angle
        self.border_style = border_style
        self.outline = outline
        self.shadow = shadow
        self.alignment = alignment #1: 底部左对齐 2: 底部居中 3: 底部右对齐 4: 中部左对齐 5: 中部居中 6: 中部右对齐 7: 顶部左对齐 8: 顶部居中 9: 顶部右对齐
        self.margin_l = margin_l
        self.margin_r = margin_r
        self.margin_v = margin_v
        self.encoding = encoding
        if segmenter_path is not None:
            self.segmenter = Segmenter(segmenter_path) #用于重新分词 

    def split_vtt(self, output):
        """Process a VTT file to split subtitle lines based on spaces and adjust timings."""
        with open(self.vtt_path , 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            if re.match(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', line):
                start_time, end_time = line.split(' --> ')
                i += 1
                text = lines[i].strip()
                new_subtitles = split_subtitle_line(start_time, end_time, text)
                for new_start, new_end, new_text in new_subtitles:
                    new_lines.append(f"{new_start} --> {new_end}\n")
                    new_lines.append(f"{new_text}\n"+"\n")
            else:
                new_lines.append(line + '\n')
            
            i += 1
        
        with open(output, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)

        replace_file(self.vtt_path, output)        


    def format_vtt_file(self, output_path):
        vtt_text = ""
        with open(self.vtt_path, 'r', encoding='utf-8') as f:
            vtt_text = f.read()
        vtt_text = re.sub(r"\n(?!\n)", "", vtt_text)
        vtt = webvtt.from_string(vtt_text)

        cleaned_captions = []

        for caption in vtt:
            # 如果包含汉字 删除不必要的换行并删除文字中的空格
            cleaned_text = caption.text
            if util.contains_chinese(caption.text):
                cleaned_text = caption.text.replace(" ", "")
                if self.segmenter is not None: #重新分词
                    cleaned_text = self.segmenter.segment(cleaned_text)
            cleaned_captions.append((caption.start, caption.end, cleaned_text))

        # 创建并写入新的VTT文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            for start, end, text in cleaned_captions:
                f.write(f"{start} --> {end}\n{text}\n\n")
        
        replace_file(self.vtt_path, output_path)


    def convert_vtt_to_ass(self, output_path):
        vtt = webvtt.read(self.vtt_path)
        ass_content = self._generate_ass_header()
        ass_content += "[Events]\n"
        ass_content += "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"

        for caption in vtt:
            start = self._convert_timestamp(caption.start)
            end = self._convert_timestamp(caption.end)
            text = caption.text.replace("\n", "\\N")

            style_start = "{"
            style_end = "}"
            show_animation = "\\t(0,"+str(Config().subtitle_cli["show_duration"])+",\\fscx"+str(Config().subtitle_cli["size_ratio"])+"\\fscy"+str(Config().subtitle_cli["size_ratio"])+")" 
            fad_out = "\\fad(0,"+str(Config().subtitle_cli["fad_out"])+")"
            font_borader_style = "\\bord4\\3c&H000000&"
            text = style_start +show_animation + fad_out + style_end + style_start + font_borader_style + style_end + text
            
            
            ass_content += f"Dialogue: 0,{start},{end},{self.name},,0,0,0,,{text}\n"

        with open(output_path, 'w', encoding='utf-8-sig') as f:
            f.write(ass_content)

    def _generate_ass_header(self):
        header = "[Script Info]\n"
        header += "ScriptType: v4.00+\n"
        header += "Collisions: Normal\n"
        header += "PlayDepth: 0\n"
        header += "\n"
        header += "[V4+ Styles]\n"
        header += "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        header += f"Style: {self.name},{self.fontname},{self.fontsize},{self.primary_colour},{self.secondary_colour},{self.outline_colour},{self.back_colour},{self.bold},{self.italic},{self.underline},{self.strikeout},{self.scale_x},{self.scale_y},{self.spacing},{self.angle},{self.border_style},{self.outline},{self.shadow},{self.alignment},{self.margin_l},{self.margin_r},{self.margin_v},{self.encoding}\n"
        return header

    def _convert_timestamp(self, timestamp):
        hours, minutes, seconds = timestamp.split(':')
        seconds, milliseconds = seconds.split('.')
        milliseconds = round(int(milliseconds) / 10)  # Convert milliseconds to centiseconds
        return f"{int(hours):01d}:{int(minutes):02d}:{int(seconds):02d}.{int(milliseconds):02d}"


def parse_vtt_time(time_str):
    """Parse a VTT time string into a timedelta object."""
    hours, minutes, seconds_milliseconds = time_str.split(':')
    seconds, milliseconds = map(int, seconds_milliseconds.split('.'))
    return timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds), milliseconds=milliseconds)

def format_vtt_time(td):
    """Format a timedelta object into a VTT time string."""
    total_seconds = int(td.total_seconds())
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

def split_subtitle_line(start_time, end_time, text):
    """Split a subtitle line into multiple lines based on spaces and adjust timings."""
    words = text.split()
    total_words = len(words)
    total_fonts = len(text.replace(" ", ""))
    
    start_td = parse_vtt_time(start_time)
    end_td = parse_vtt_time(end_time)
    total_duration = end_td - start_td
    
    new_subtitles = []
    current_start = start_td
    current_text = ''
    
    for i, word in enumerate(words):
        if current_text:
            current_text += ' ' + word
        else:
            current_text = word
        
        if i == total_words - 1 or current_text.count(' ') >= 0:
            # word_count = len(current_text.split())
            # current_duration = total_duration * (word_count / total_words)
            current_duration = total_duration * (len(word) / total_fonts)
            current_end = current_start + current_duration
            
            new_subtitles.append((format_vtt_time(current_start), format_vtt_time(current_end), current_text))
            
            current_start = current_end
            current_text = ''
    
    return new_subtitles


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