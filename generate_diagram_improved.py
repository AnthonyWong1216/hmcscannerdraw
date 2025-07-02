#!/usr/bin/env python3
"""
Improved script to generate network diagrams with better layout and no overlapping.
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont
import string

class ImprovedNetworkDiagramGenerator:
    def __init__(self, config_data):
        self.config_data = config_data
        self.width = 700
        self.height = 400
        self.margin = 60
        self.box_width = 120
        self.box_height = 35
        self.line_spacing = 20
        self.component_spacing = 25
        
        # Colors
        self.hostname_color = (70, 130, 180)  # Steel blue
        self.sea_color = (255, 165, 0)        # Orange
        self.etherchannel_color = (50, 205, 50)  # Lime green
        self.real_adapter_color = (255, 69, 0)   # Red orange
        self.virtual_adapter_color = (138, 43, 226)  # Blue violet
        self.line_color = (0, 0, 0)           # Black
        self.text_color = (255, 255, 255)     # White
        
    def calculate_text_width(self, text, font):
        """Calculate the width needed for text."""
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]
    
    def calculate_box_width(self, text, font, min_width=None):
        """Calculate appropriate box width based on text."""
        text_width = self.calculate_text_width(text, font)
        padding = 12  # Small padding
        width = text_width + padding
        if min_width:
            width = max(width, min_width)
        return width
    
    def draw_color_legend(self, draw, y, font):
        legend_items = [
            (self.sea_color, 'SEA (Shared Ethernet Adapter)'),
            (self.etherchannel_color, 'Etherchannel adapter(s)'),
            (self.real_adapter_color, 'Real adapter(s)'),
            (self.virtual_adapter_color, 'Virtual adapter(s)'),
        ]
        x = self.margin
        box = 18
        spacing = 12
        for color, label in legend_items:
            draw.rectangle([x, y, x+box, y+box], fill=color, outline=(0,0,0), width=1)
            draw.text((x+box+6, y), label, fill=(0,0,0), font=font)
            x += box + spacing + self.calculate_text_width(label, font) + 30

    def create_diagram(self, output_path, sea_group, hostname, legend_font):
        img = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        # Layout: all SEAs horizontally, centered
        n = len(sea_group)
        if n == 0:
            img.save(output_path)
            return
        total_sea_width = sum(self.calculate_box_width(sea.get('sea_name', 'Unknown SEA'), legend_font) for sea in sea_group) + (n-1)*100
        start_x = (self.width - total_sea_width) // 2
        sea_y = 80
        sea_positions = []
        x = start_x
        for sea in sea_group:
            sea_name = sea.get('sea_name', 'Unknown SEA')
            sea_width = self.calculate_box_width(sea_name, legend_font)
            self.draw_box(draw, x, sea_y, sea_width, self.box_height, self.sea_color, sea_name, legend_font)
            sea_positions.append((x, sea_y, sea_width))
            x += sea_width + 100
        # Draw components for each SEA
        for (sea, (sea_x, sea_y, sea_width)) in zip(sea_group, sea_positions):
            self.draw_sea_components_improved(draw, sea, sea_x, sea_y, sea_width, legend_font)
        # Draw color legend at the bottom
        legend_y = self.height - self.margin - 30
        self.draw_color_legend(draw, legend_y, legend_font)
        img.save(output_path)
        print(f"Saved: {output_path}")

    def calculate_sea_component_height(self, sea, font):
        """Calculate the total height needed for SEA components."""
        height = 0
        
        # ETHERCHANNEL
        etherchannel = sea.get('etherchannel')
        if etherchannel and etherchannel.get('adapters'):
            height += self.box_height + self.component_spacing
        
        # REAL ADAPTERS
        real_adapters = sea.get('real_adapters', [])
        if real_adapters:
            # Group adapters by hardware path
            hw_paths = {}
            for adapter in real_adapters:
                hw_path = adapter.get('hardware_path', 'Unknown')
                if hw_path not in hw_paths:
                    hw_paths[hw_path] = []
                hw_paths[hw_path].append(adapter['adapter_name'])
            
            for hw_path, adapter_names in hw_paths.items():
                height += self.box_height + 8
        
        # VIRTUAL ADAPTERS
        virtual_adapters = sea.get('virtual_adapters', [])
        if virtual_adapters:
            # Group adapters by hardware path
            hw_paths = {}
            for adapter in virtual_adapters:
                hw_path = adapter.get('hardware_path', 'Unknown')
                if hw_path not in hw_paths:
                    hw_paths[hw_path] = []
                hw_paths[hw_path].append(adapter['adapter_name'])
            
            for hw_path, adapter_names in hw_paths.items():
                height += self.box_height + 8
        
        return height
    
    def draw_vertical_dogleg(self, draw, parent_x, parent_y, parent_width, parent_height, child_x, child_y, child_width):
        # Start at bottom center of parent
        start_x = parent_x + parent_width // 2
        start_y = parent_y + parent_height
        # End at top center of child
        end_x = child_x + child_width // 2
        end_y = child_y
        # Draw short vertical down from parent
        mid_y1 = start_y + 10
        # Draw short vertical up to child
        mid_y2 = end_y - 10
        # Draw lines
        draw.line([start_x, start_y, start_x, mid_y1], fill=self.line_color, width=1)
        draw.line([start_x, mid_y1, end_x, mid_y2], fill=self.line_color, width=1)
        draw.line([end_x, mid_y2, end_x, end_y], fill=self.line_color, width=1)

    def draw_sea_components_improved(self, draw, sea, sea_x, sea_y, sea_width, font):
        components_y = sea_y + self.box_height + self.component_spacing
        # ETHERCHANNEL
        etherchannel = sea.get('etherchannel')
        if etherchannel and etherchannel.get('adapters'):
            etherchannel_x = sea_x - 40
            etherchannel_y = components_y
            adapter_names = ', '.join(etherchannel['adapters'][:2])
            if len(etherchannel['adapters']) > 2:
                adapter_names += "..."
            etherchannel_text = f"{adapter_names}"
            etherchannel_width = self.calculate_box_width(etherchannel_text, font)
            self.draw_box(draw, etherchannel_x, etherchannel_y, etherchannel_width, self.box_height,
                         self.etherchannel_color, etherchannel_text, font)
            self.draw_vertical_dogleg(draw, sea_x, sea_y, sea_width, self.box_height, etherchannel_x, etherchannel_y, etherchannel_width)
            components_y += self.box_height + self.component_spacing
        # REAL ADAPTERS (spread horizontally)
        real_adapters = sea.get('real_adapters', [])
        if real_adapters:
            hw_paths = {}
            for adapter in real_adapters:
                hw_path = adapter.get('hardware_path', 'Unknown')
                if hw_path not in hw_paths:
                    hw_paths[hw_path] = []
                hw_paths[hw_path].append(adapter['adapter_name'])
            adapter_boxes = []
            for hw_path, adapter_names in hw_paths.items():
                adapter_text = ', '.join(adapter_names[:2])
                if len(adapter_names) > 2:
                    adapter_text += "..."
                width = self.calculate_box_width(adapter_text, font)
                adapter_boxes.append((adapter_text, width))
            total_width = sum(w for _, w in adapter_boxes) + (len(adapter_boxes)-1)*18
            start_x = sea_x + sea_width//2 - total_width//2
            y = components_y
            for i, (adapter_text, width) in enumerate(adapter_boxes):
                x = start_x + sum(adapter_boxes[j][1] for j in range(i)) + i*18
                self.draw_box(draw, x, y, width, self.box_height, self.real_adapter_color, adapter_text, font)
                if etherchannel and etherchannel.get('adapters'):
                    self.draw_vertical_dogleg(draw, etherchannel_x, etherchannel_y, etherchannel_width, self.box_height, x, y, width)
                else:
                    self.draw_vertical_dogleg(draw, sea_x, sea_y, sea_width, self.box_height, x, y, width)
            components_y += self.box_height + 8
        # VIRTUAL ADAPTERS (spread horizontally above SEA)
        virtual_adapters = sea.get('virtual_adapters', [])
        if virtual_adapters:
            hw_paths = {}
            for adapter in virtual_adapters:
                hw_path = adapter.get('hardware_path', 'Unknown')
                if hw_path not in hw_paths:
                    hw_paths[hw_path] = []
                hw_paths[hw_path].append(adapter['adapter_name'])
            adapter_boxes = []
            for hw_path, adapter_names in hw_paths.items():
                adapter_text = ', '.join(adapter_names[:2])
                if len(adapter_names) > 2:
                    adapter_text += "..."
                width = self.calculate_box_width(adapter_text, font)
                adapter_boxes.append((adapter_text, width))
            total_width = sum(w for _, w in adapter_boxes) + (len(adapter_boxes)-1)*18
            y = sea_y - self.box_height - self.component_spacing
            start_x = sea_x + sea_width//2 - total_width//2
            for i, (adapter_text, width) in enumerate(adapter_boxes):
                x = start_x + sum(adapter_boxes[j][1] for j in range(i)) + i*18
                self.draw_box(draw, x, y, width, self.box_height, self.virtual_adapter_color, adapter_text, font)
                self.draw_vertical_dogleg(draw, x, y, width, self.box_height, sea_x, sea_y, sea_width)
    
    def draw_box(self, draw, x, y, width, height, color, text, font):
        """Draw a box with text."""
        # Draw rectangle
        draw.rectangle([x, y, x + width, y + height], fill=color, outline=self.line_color, width=1)
        
        # Draw text (centered)
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = x + (width - text_width) // 2
        text_y = y + (height - text_height) // 2
        
        draw.text((text_x, text_y), text, fill=self.text_color, font=font)
    
    def draw_line(self, draw, x1, y1, x2, y2):
        """Draw a line between two points."""
        draw.line([x1, y1, x2, y2], fill=self.line_color, width=1)

def main():
    """Main function to generate improved network diagrams."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'outputfile')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    config_file = os.path.join(script_dir, "network_config_fixed.json")
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found.")
        print("Please run extract_network_config_fixed.py first.")
        exit(1)
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    try:
        legend_font = ImageFont.truetype("arial.ttf", 11)
    except:
        from PIL import ImageFont
        legend_font = ImageFont.load_default()
    generator = ImprovedNetworkDiagramGenerator(config_data)
    for config in config_data:
        hostname = config.get('hostname', 'unknown')
        sea_sections = config.get('sea_sections', [])
        # Split into groups of 3
        for idx, i in enumerate(range(0, len(sea_sections), 3)):
            group = sea_sections[i:i+3]
            suffix = string.ascii_lowercase[idx]
            outname = f"network_diagram_{hostname}_{suffix}.png"
            outpath = os.path.join(output_dir, outname)
            generator.create_diagram(outpath, group, hostname, legend_font)

if __name__ == "__main__":
    main() 