#!/usr/bin/env python3
"""
Advanced script to generate network diagrams with collision detection and automatic layout adjustment.
"""

import json
import os
import math
from PIL import Image, ImageDraw, ImageFont

class AdvancedNetworkDiagramGenerator:
    def __init__(self, config_data):
        self.config_data = config_data
        self.width = 1800
        self.height = 1400
        self.margin = 80
        self.box_width = 100
        self.box_height = 30
        self.line_spacing = 15
        self.component_spacing = 30
        self.min_spacing = 10
        
        # Colors
        self.hostname_color = (70, 130, 180)  # Steel blue
        self.sea_color = (255, 165, 0)        # Orange
        self.etherchannel_color = (50, 205, 50)  # Lime green
        self.real_adapter_color = (255, 69, 0)   # Red orange
        self.virtual_adapter_color = (138, 43, 226)  # Blue violet
        self.line_color = (0, 0, 0)           # Black
        self.text_color = (255, 255, 255)     # White
        
        # Track all placed boxes to prevent overlapping
        self.placed_boxes = []
        
    def calculate_text_width(self, text, font):
        """Calculate the width needed for text."""
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]
    
    def calculate_box_width(self, text, font, min_width=None):
        """Calculate appropriate box width based on text."""
        text_width = self.calculate_text_width(text, font)
        padding = 16  # Extra padding around text
        width = text_width + padding
        if min_width:
            width = max(width, min_width)
        return width
    
    def check_collision(self, x, y, width, height):
        """Check if a box would collide with any existing boxes."""
        for box in self.placed_boxes:
            bx, by, bw, bh = box
            # Check for overlap
            if not (x + width < bx or bx + bw < x or y + height < by or by + bh < y):
                return True
        return False
    
    def find_free_position(self, desired_x, desired_y, width, height, max_attempts=50):
        """Find a free position for a box, starting from desired position."""
        if not self.check_collision(desired_x, desired_y, width, height):
            return desired_x, desired_y
        
        # Try positions around the desired location
        for attempt in range(max_attempts):
            # Spiral outward from desired position
            radius = (attempt + 1) * self.min_spacing
            angle = attempt * 0.5
            
            offset_x = int(radius * math.cos(angle))
            offset_y = int(radius * math.sin(angle))
            
            new_x = desired_x + offset_x
            new_y = desired_y + offset_y
            
            # Ensure box stays within image bounds
            if (new_x >= self.margin and new_x + width <= self.width - self.margin and
                new_y >= self.margin and new_y + height <= self.height - self.margin):
                if not self.check_collision(new_x, new_y, width, height):
                    return new_x, new_y
        
        # If no free position found, return the original position
        return desired_x, desired_y
    
    def add_box(self, x, y, width, height):
        """Add a box to the placed boxes list."""
        self.placed_boxes.append((x, y, width, height))
    
    def create_diagram(self, output_path):
        """Create the network diagram with advanced layout."""
        # Create image
        img = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font, fallback to basic if not available
        try:
            font_large = ImageFont.truetype("arial.ttf", 11)
            font_medium = ImageFont.truetype("arial.ttf", 9)
            font_small = ImageFont.truetype("arial.ttf", 7)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        y_offset = self.margin
        
        for config in self.config_data:
            hostname = config.get('hostname', 'Unknown')
            sea_sections = config.get('sea_sections', [])
            
            # Calculate hostname box width
            hostname_width = self.calculate_box_width(hostname, font_large, self.box_width)
            
            # Draw hostname box at the top
            hostname_x = (self.width - hostname_width) // 2
            hostname_y = y_offset
            
            # Check for collision and adjust if needed
            hostname_x, hostname_y = self.find_free_position(hostname_x, hostname_y, hostname_width, self.box_height)
            self.add_box(hostname_x, hostname_y, hostname_width, self.box_height)
            
            self.draw_box(draw, hostname_x, hostname_y, hostname_width, self.box_height, 
                         self.hostname_color, hostname, font_large)
            
            y_offset += self.box_height + 50
            
            # Calculate layout for SEA sections
            sea_count = len(sea_sections)
            if sea_count > 0:
                # Calculate spacing to fit all SEAs with proper spacing
                available_width = self.width - 2 * self.margin
                sea_spacing = min(available_width // sea_count, 180)
                sea_start_x = (self.width - (sea_count - 1) * sea_spacing) // 2
                
                # Calculate maximum height needed for this hostname's components
                max_component_height = 0
                
                for i, sea in enumerate(sea_sections):
                    sea_x = sea_start_x + i * sea_spacing
                    sea_y = y_offset
                    
                    # Calculate SEA box width
                    sea_name = sea.get('sea_name', 'Unknown SEA')
                    sea_width = self.calculate_box_width(sea_name, font_medium, self.box_width)
                    
                    # Check for collision and adjust if needed
                    sea_x, sea_y = self.find_free_position(sea_x, sea_y, sea_width, self.box_height)
                    self.add_box(sea_x, sea_y, sea_width, self.box_height)
                    
                    # Calculate component heights for this SEA
                    component_height = self.calculate_sea_component_height(sea, font_small)
                    max_component_height = max(max_component_height, component_height)
                    
                    # Draw SEA box
                    self.draw_box(draw, sea_x, sea_y, sea_width, self.box_height, 
                                 self.sea_color, sea_name, font_medium)
                    
                    # Draw connections and components
                    self.draw_sea_components_advanced(draw, sea, sea_x, sea_y, sea_width, font_small)
                    
                    # Connect hostname to SEA
                    self.draw_line(draw, 
                                 hostname_x + hostname_width // 2, hostname_y + self.box_height,
                                 sea_x + sea_width // 2, sea_y)
                
                # Update y_offset for next hostname
                y_offset += self.box_height + max_component_height + 80
        
        # Save the image
        img.save(output_path)
        print(f"Advanced network diagram saved to: {output_path}")
    
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
                height += self.box_height + 6
        
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
                height += self.box_height + 6
        
        return height
    
    def draw_sea_components_advanced(self, draw, sea, sea_x, sea_y, sea_width, font):
        """Draw components for a specific SEA with advanced layout."""
        components_y = sea_y + self.box_height + self.component_spacing
        
        # Draw ETHERCHANNEL if exists
        etherchannel = sea.get('etherchannel')
        etherchannel_x = None
        etherchannel_y = None
        etherchannel_width = None
        
        if etherchannel and etherchannel.get('adapters'):
            etherchannel_x = sea_x - 35
            etherchannel_y = components_y
            
            adapter_names = ', '.join(etherchannel['adapters'][:2])  # Limit to first 2
            if len(etherchannel['adapters']) > 2:
                adapter_names += "..."
            
            etherchannel_text = f"EC: {adapter_names}"
            etherchannel_width = self.calculate_box_width(etherchannel_text, font, self.box_width)
            
            # Check for collision and adjust if needed
            etherchannel_x, etherchannel_y = self.find_free_position(etherchannel_x, etherchannel_y, etherchannel_width, self.box_height)
            self.add_box(etherchannel_x, etherchannel_y, etherchannel_width, self.box_height)
            
            self.draw_box(draw, etherchannel_x, etherchannel_y, etherchannel_width, self.box_height,
                         self.etherchannel_color, etherchannel_text, font)
            
            # Connect SEA to ETHERCHANNEL
            self.draw_line(draw, 
                         sea_x + sea_width // 2, sea_y + self.box_height,
                         etherchannel_x + etherchannel_width // 2, etherchannel_y)
            
            components_y += self.box_height + self.component_spacing
        
        # Draw REAL ADAPTERS
        real_adapters = sea.get('real_adapters', [])
        if real_adapters:
            real_adapters_x = sea_x - 35
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
                
                real_adapter_width = self.calculate_box_width(adapter_text, font, self.box_width)
                
                # Check for collision and adjust if needed
                real_adapters_x, real_adapters_y = self.find_free_position(real_adapters_x, real_adapters_y, real_adapter_width, self.box_height)
                self.add_box(real_adapters_x, real_adapters_y, real_adapter_width, self.box_height)
                
                self.draw_box(draw, real_adapters_x, real_adapters_y, real_adapter_width, self.box_height,
                             self.real_adapter_color, adapter_text, font)
                
                # Connect to SEA or ETHERCHANNEL
                if etherchannel and etherchannel.get('adapters') and etherchannel_x is not None:
                    # Connect to ETHERCHANNEL
                    self.draw_line(draw,
                                 etherchannel_x + etherchannel_width // 2, etherchannel_y + self.box_height,
                                 real_adapters_x + real_adapter_width // 2, real_adapters_y)
                else:
                    # Connect directly to SEA
                    self.draw_line(draw,
                                 sea_x + sea_width // 2, sea_y + self.box_height,
                                 real_adapters_x + real_adapter_width // 2, real_adapters_y)
                
                real_adapters_y += self.box_height + 6
        
        # Draw VIRTUAL ADAPTERS (above SEA)
        virtual_adapters = sea.get('virtual_adapters', [])
        if virtual_adapters:
            virtual_adapters_x = sea_x + 35
            virtual_adapters_y = sea_y - self.box_height - self.component_spacing
            
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
                
                virtual_adapter_width = self.calculate_box_width(adapter_text, font, self.box_width)
                
                # Check for collision and adjust if needed
                virtual_adapters_x, virtual_adapters_y = self.find_free_position(virtual_adapters_x, virtual_adapters_y, virtual_adapter_width, self.box_height)
                self.add_box(virtual_adapters_x, virtual_adapters_y, virtual_adapter_width, self.box_height)
                
                self.draw_box(draw, virtual_adapters_x, virtual_adapters_y, virtual_adapter_width, self.box_height,
                             self.virtual_adapter_color, adapter_text, font)
                
                # Connect to SEA
                self.draw_line(draw,
                             virtual_adapters_x + virtual_adapter_width // 2, virtual_adapters_y + self.box_height,
                             sea_x + sea_width // 2, sea_y)
                
                virtual_adapters_y -= self.box_height + 6
    
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
    """Main function to generate advanced network diagrams."""
    
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
    
    # Generate advanced diagram
    generator = AdvancedNetworkDiagramGenerator(config_data)
    output_path = os.path.join(script_dir, "network_diagram_advanced.png")
    generator.create_diagram(output_path)

if __name__ == "__main__":
    main() 