#!/usr/bin/env python3
"""
Script to generate network diagrams from the fixed network configuration.
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont

class NetworkDiagramGenerator:
    def __init__(self, config_data):
        self.config_data = config_data
        self.width = 1400
        self.height = 1000
        self.margin = 50
        self.box_width = 180
        self.box_height = 50
        
        # Colors
        self.hostname_color = (70, 130, 180)  # Steel blue
        self.sea_color = (255, 165, 0)        # Orange
        self.etherchannel_color = (50, 205, 50)  # Lime green
        self.real_adapter_color = (255, 69, 0)   # Red orange
        self.virtual_adapter_color = (138, 43, 226)  # Blue violet
        self.line_color = (0, 0, 0)           # Black
        self.text_color = (255, 255, 255)     # White
        
    def create_diagram(self, output_path):
        """Create the network diagram."""
        # Create image
        img = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font, fallback to basic if not available
        try:
            font_large = ImageFont.truetype("arial.ttf", 14)
            font_medium = ImageFont.truetype("arial.ttf", 10)
            font_small = ImageFont.truetype("arial.ttf", 8)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        y_offset = self.margin
        
        for config in self.config_data:
            hostname = config.get('hostname', 'Unknown')
            sea_sections = config.get('sea_sections', [])
            
            # Draw hostname box at the top
            hostname_x = (self.width - self.box_width) // 2
            hostname_y = y_offset
            self.draw_box(draw, hostname_x, hostname_y, self.box_width, self.box_height, 
                         self.hostname_color, hostname, font_large)
            
            y_offset += self.box_height + 30
            
            # Calculate layout for SEA sections
            sea_count = len(sea_sections)
            if sea_count > 0:
                # Calculate spacing to fit all SEAs
                available_width = self.width - 2 * self.margin
                sea_spacing = min(available_width // sea_count, 250)
                sea_start_x = (self.width - (sea_count - 1) * sea_spacing) // 2
                
                for i, sea in enumerate(sea_sections):
                    sea_x = sea_start_x + i * sea_spacing
                    sea_y = y_offset
                    
                    # Draw SEA box
                    sea_name = sea.get('sea_name', 'Unknown SEA')
                    self.draw_box(draw, sea_x, sea_y, self.box_width, self.box_height, 
                                 self.sea_color, sea_name, font_medium)
                    
                    # Draw connections and components
                    self.draw_sea_components(draw, sea, sea_x, sea_y, font_small)
                    
                    # Connect hostname to SEA
                    self.draw_line(draw, 
                                 hostname_x + self.box_width // 2, hostname_y + self.box_height,
                                 sea_x + self.box_width // 2, sea_y)
                
                # Update y_offset for next hostname
                y_offset += self.box_height + 150
        
        # Save the image
        img.save(output_path)
        print(f"Network diagram saved to: {output_path}")
    
    def draw_sea_components(self, draw, sea, sea_x, sea_y, font):
        """Draw components for a specific SEA."""
        components_y = sea_y + self.box_height + 15
        
        # Draw ETHERCHANNEL if exists
        etherchannel = sea.get('etherchannel')
        if etherchannel and etherchannel.get('adapters'):
            etherchannel_x = sea_x - 30
            etherchannel_y = components_y
            adapter_names = ', '.join(etherchannel['adapters'][:3])  # Limit to first 3
            if len(etherchannel['adapters']) > 3:
                adapter_names += "..."
            self.draw_box(draw, etherchannel_x, etherchannel_y, self.box_width, self.box_height,
                         self.etherchannel_color, f"EC: {adapter_names}", font)
            
            # Connect SEA to ETHERCHANNEL
            self.draw_line(draw, 
                         sea_x + self.box_width // 2, sea_y + self.box_height,
                         etherchannel_x + self.box_width // 2, etherchannel_y)
            
            components_y += self.box_height + 15
        
        # Draw REAL ADAPTERS
        real_adapters = sea.get('real_adapters', [])
        if real_adapters:
            real_adapters_x = sea_x - 30
            real_adapters_y = components_y
            
            # Group adapters by hardware path
            hw_paths = {}
            for adapter in real_adapters:
                hw_path = adapter.get('hardware_path', 'Unknown')
                if hw_path not in hw_paths:
                    hw_paths[hw_path] = []
                hw_paths[hw_path].append(adapter['adapter_name'])
            
            # Draw each hardware path group
            for hw_path, adapter_names in hw_paths.items():
                adapter_text = f"RA: {', '.join(adapter_names[:2])}"  # Limit to first 2
                if len(adapter_names) > 2:
                    adapter_text += "..."
                self.draw_box(draw, real_adapters_x, real_adapters_y, self.box_width, self.box_height,
                             self.real_adapter_color, adapter_text, font)
                
                # Connect to SEA or ETHERCHANNEL
                if etherchannel and etherchannel.get('adapters'):
                    # Connect to ETHERCHANNEL
                    self.draw_line(draw,
                                 etherchannel_x + self.box_width // 2, etherchannel_y + self.box_height,
                                 real_adapters_x + self.box_width // 2, real_adapters_y)
                else:
                    # Connect directly to SEA
                    self.draw_line(draw,
                                 sea_x + self.box_width // 2, sea_y + self.box_height,
                                 real_adapters_x + self.box_width // 2, real_adapters_y)
                
                real_adapters_y += self.box_height + 8
        
        # Draw VIRTUAL ADAPTERS (above SEA)
        virtual_adapters = sea.get('virtual_adapters', [])
        if virtual_adapters:
            virtual_adapters_x = sea_x + 30
            virtual_adapters_y = sea_y - self.box_height - 15
            
            # Group adapters by hardware path
            hw_paths = {}
            for adapter in virtual_adapters:
                hw_path = adapter.get('hardware_path', 'Unknown')
                if hw_path not in hw_paths:
                    hw_paths[hw_path] = []
                hw_paths[hw_path].append(adapter['adapter_name'])
            
            # Draw each hardware path group
            for hw_path, adapter_names in hw_paths.items():
                adapter_text = f"VA: {', '.join(adapter_names[:2])}"  # Limit to first 2
                if len(adapter_names) > 2:
                    adapter_text += "..."
                self.draw_box(draw, virtual_adapters_x, virtual_adapters_y, self.box_width, self.box_height,
                             self.virtual_adapter_color, adapter_text, font)
                
                # Connect to SEA
                self.draw_line(draw,
                             virtual_adapters_x + self.box_width // 2, virtual_adapters_y + self.box_height,
                             sea_x + self.box_width // 2, sea_y)
                
                virtual_adapters_y -= self.box_height + 8
    
    def draw_box(self, draw, x, y, width, height, color, text, font):
        """Draw a box with text."""
        # Draw rectangle
        draw.rectangle([x, y, x + width, y + height], fill=color, outline=self.line_color, width=2)
        
        # Draw text (centered)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = x + (width - text_width) // 2
        text_y = y + (height - text_height) // 2
        
        draw.text((text_x, text_y), text, fill=self.text_color, font=font)
    
    def draw_line(self, draw, x1, y1, x2, y2):
        """Draw a line between two points."""
        draw.line([x1, y1, x2, y2], fill=self.line_color, width=2)

def main():
    """Main function to generate network diagrams."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "network_config_fixed.json")
    
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found.")
        print("Please run extract_network_config_fixed.py first.")
        return
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"Error reading configuration file: {e}")
        return
    
    if not config_data:
        print("No configuration data found.")
        return
    
    # Generate diagram
    generator = NetworkDiagramGenerator(config_data)
    output_path = os.path.join(script_dir, "network_diagram.png")
    generator.create_diagram(output_path)

if __name__ == "__main__":
    main() 