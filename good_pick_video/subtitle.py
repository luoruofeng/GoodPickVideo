import webvtt
import re

class SubtitleConverter:
    def __init__(self, vtt_path, name="Default", fontname="Arial", fontsize=20, primary_colour="&H00FFFFFF", secondary_colour="&H000000FF", outline_colour="&H00000000", back_colour="&H64000000", bold=-1, italic=0, underline=0, strikeout=0, scale_x=100, scale_y=100, spacing=0, angle=0, border_style=1, outline=1, shadow=0, alignment=2, margin_l=10, margin_r=10, margin_v=10, encoding=1):
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
        self.alignment = alignment
        self.margin_l = margin_l
        self.margin_r = margin_r
        self.margin_v = margin_v
        self.encoding = encoding


    def format_vtt_file(self, output_path):
        vtt_text = ""
        with open(self.vtt_path, 'r', encoding='utf-8') as f:
            vtt_text = f.read()
        vtt_text = re.sub(r"\n(?!\n)", "", vtt_text)
        vtt = webvtt.from_string(vtt_text)

        cleaned_captions = []

        for caption in vtt:
            # 删除不必要的换行并删除文字中的空格
            cleaned_text = caption.text.replace(" ", "")
            cleaned_captions.append((caption.start, caption.end, cleaned_text))

        # 创建并写入新的VTT文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            for start, end, text in cleaned_captions:
                f.write(f"{start} --> {end}\n{text}\n\n")
        
        self.vtt_path = output_path

    def convert_vtt_to_ass(self, output_path):
        vtt = webvtt.read(self.vtt_path)
        ass_content = self._generate_ass_header()
        ass_content += "[Events]\n"
        ass_content += "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"

        for caption in vtt:
            start = self._convert_timestamp(caption.start)
            end = self._convert_timestamp(caption.end)
            text = caption.text.replace("\n", "\\N")
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

