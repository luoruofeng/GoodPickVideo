from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio
import os
import math

class GifCreator:
    def __init__(self, font_path='SourceHanSans-Normal.ttf', font_size=20, total_duration=1.0,
                 text_color='#000000', outline_color='#FFFFFF', outline_width=1,
                 bg_color='#C8C8C8', bg_outline_color='#000000', bg_outline_width=1,
                 num_frames=10, padding=10, bg_shape='rectangle'):
        self.font_path = font_path
        self.font_size = font_size
        self.total_duration = total_duration
        self.text_color = self.hex_to_rgb(text_color)
        self.outline_color = self.hex_to_rgb(outline_color)
        self.outline_width = outline_width
        self.bg_color = self.hex_to_rgb(bg_color)
        self.bg_outline_color = self.hex_to_rgb(bg_outline_color)
        self.bg_outline_width = bg_outline_width
        self.num_frames = num_frames
        self.padding = padding
        self.bg_shape = bg_shape

    @staticmethod
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)

    def draw_text_with_outline(self, draw, text, font, position, text_color, outline_color, outline_width):
        x, y = position
        # Draw outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        # Draw text
        draw.text((x, y), text, font=font, fill=text_color)

    def draw_background(self, draw, shape, panel_size, fill_color, outline_color, outline_width):
        width, height = panel_size
        if shape == 'rectangle':
            draw.rectangle([0, 0, width, height], fill=fill_color, outline=outline_color, width=outline_width)
        elif shape == 'ellipse':
            draw.ellipse([0, 0, width, height], fill=fill_color, outline=outline_color, width=outline_width)
        elif shape == 'star':
            num_points = 5  # You can customize this for different star shapes
            points = []
            for i in range(2 * num_points):
                angle = i * math.pi / num_points
                r = (width / 2) if i % 2 == 0 else (width / 4)
                x = width / 2 + r * math.cos(angle)
                y = height / 2 + r * math.sin(angle)
                points.append((x, y))
            draw.polygon(points, fill=fill_color, outline=outline_color, width=outline_width)

    def create_text_gif(self, text, output_path='output.gif'):
        base_font_size = self.font_size
        max_font_size = int(base_font_size * 1.3)
        font = ImageFont.truetype(self.font_path, max_font_size)
        text_width, text_height = font.getsize(text)
        
        # Calculate the size of the background panel
        panel_width = text_width + 2 * self.padding
        panel_height = text_height + 2 * self.padding
        
        frames = []
        
        for i in range(self.num_frames):
            image = Image.new('RGBA', (panel_width, panel_height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(image)
            
            current_font_size = int(base_font_size * (1 + 0.3 * math.sin(math.pi * i / (self.num_frames / 2))))
            font = ImageFont.truetype(self.font_path, current_font_size)
            
            text_width, text_height = draw.textsize(text, font=font)
            x = (panel_width - text_width) / 2
            y = (panel_height - text_height) / 2
            
            # Draw background panel with outline
            self.draw_background(draw, self.bg_shape, (panel_width, panel_height), self.bg_color, self.bg_outline_color, self.bg_outline_width)
            
            self.draw_text_with_outline(draw, text, font, (x, y), self.text_color, self.outline_color, self.outline_width)
            
            frames.append(image)
        
        # Calculate the frame duration
        frame_duration = self.total_duration / self.num_frames
        
        # Save frames as GIF
        frame_paths = []
        for i, frame in enumerate(frames):
            frame_path = f'frame_{i}.png'
            frame.save(frame_path)
            frame_paths.append(frame_path)
        
        with imageio.get_writer(output_path, mode='I', duration=frame_duration) as writer:
            for frame_path in frame_paths:
                image = imageio.imread(frame_path)
                writer.append_data(image)
        
        for frame_path in frame_paths:
            os.remove(frame_path)

        print(f"GIF saved as {output_path}")

    def resize_gif(self, input_path, output_path, new_width):
        with imageio.get_reader(input_path) as reader:
            frames = [frame for frame in reader]
            original_width, original_height = frames[0].shape[1], frames[0].shape[0]
            new_height = int((new_width / original_width) * original_height)
            resized_frames = [Image.fromarray(frame).resize((new_width, new_height), Image.ANTIALIAS) for frame in frames]
        
        with imageio.get_writer(output_path, mode='I', duration=reader.get_meta_data()['duration']) as writer:
            for frame in resized_frames:
                writer.append_data(frame)

        print(f"Resized GIF saved as {output_path}")


if __name__ == "__main__":
    # Example usage with UTF-8 encoded Chinese text
    gif_creator = GifCreator(font_path='Alibaba-PuHuiTi-Bold.ttf', font_size=150, total_duration=2.0,
                            text_color='#000000', outline_color='#000000', outline_width=0,
                            bg_color='#00FF00', bg_outline_color='#000000', bg_outline_width=22, padding=60, bg_shape='star')
    gif_creator.create_text_gif("你好，世界！", output_path='output.gif')

    # Resize the created GIF
    gif_creator.resize_gif(input_path='output.gif', output_path='output_resized.gif', new_width=200)
