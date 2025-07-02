#!/usr/bin/env python3
"""
Complete network analysis script that extracts configuration from lssea*log files
and generates network diagrams.
"""

import os
import glob
import re
import json
from collections import defaultdict

def extract_hostname_from_file(file_path):
    """Extract hostname from lssea log file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                line = line.strip()
                if line == "VIOS hostname:":
                    next_line = next(file, "").strip()
                    if next_line:
                        return next_line
        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def parse_sea_section(lines, start_idx):
    """Parse a SEA section starting from the given index."""
    sea_data = {}
    current_idx = start_idx
    
    # Find SEA line
    sea_match = None
    for i in range(current_idx, len(lines)):
        if lines[i].startswith("SEA :"):
            sea_match = re.search(r'SEA\s*:\s*(\S+)', lines[i])
            if sea_match:
                sea_data['sea_name'] = sea_match.group(1)
                current_idx = i + 1
                break
    
    if not sea_match:
        return None, start_idx
    
    # Parse SEA properties
    sea_data['properties'] = {}
    while current_idx < len(lines):
        line = lines[current_idx].strip()
        
        if line.startswith("SEA :") or line.startswith("+--") or line == "":
            break
            
        if ':' in line and not line.startswith('+'):
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                sea_data['properties'][key] = value
        
        current_idx += 1
    
    # Look for ETHERCHANNEL section
    sea_data['etherchannel'] = None
    etherchannel_start = None
    for i in range(current_idx, len(lines)):
        if "ETHERCHANNEL" in lines[i]:
            etherchannel_start = i
            break
    
    if etherchannel_start:
        sea_data['etherchannel'], current_idx = parse_etherchannel_section(lines, etherchannel_start)
    
    # Look for REAL ADAPTERS section
    sea_data['real_adapters'] = []
    real_adapters_start = None
    for i in range(current_idx, len(lines)):
        if "REAL ADAPTERS" in lines[i]:
            real_adapters_start = i
            break
    
    if real_adapters_start:
        sea_data['real_adapters'], current_idx = parse_real_adapters_section(lines, real_adapters_start)
    
    # Look for VIRTUAL ADAPTERS section
    sea_data['virtual_adapters'] = []
    virtual_adapters_start = None
    for i in range(current_idx, len(lines)):
        if "VIRTUAL ADAPTERS" in lines[i]:
            virtual_adapters_start = i
            break
    
    if virtual_adapters_start:
        sea_data['virtual_adapters'], current_idx = parse_virtual_adapters_section(lines, virtual_adapters_start)
    
    return sea_data, current_idx

def parse_etherchannel_section(lines, start_idx):
    """Parse ETHERCHANNEL section."""
    etherchannel_data = {'adapters': []}
    current_idx = start_idx + 1
    
    # Skip header lines
    while current_idx < len(lines) and (lines[current_idx].startswith('-------') or 
                                       lines[current_idx].startswith('adapter')):
        current_idx += 1
    
    # Parse adapter lines
    while current_idx < len(lines):
        line = lines[current_idx].strip()
        
        if (line.startswith("REAL ADAPTERS") or line.startswith("VIRTUAL ADAPTERS") or 
            line.startswith("+--") or line == ""):
            break
        
        if line and not line.startswith('-------'):
            parts = line.split()
            if len(parts) >= 1 and parts[0].startswith('ent'):
                adapter_name = parts[0]
                etherchannel_data['adapters'].append(adapter_name)
        
        current_idx += 1
    
    return etherchannel_data, current_idx

def parse_real_adapters_section(lines, start_idx):
    """Parse REAL ADAPTERS section."""
    real_adapters = []
    current_idx = start_idx + 1
    
    # Skip header lines
    while current_idx < len(lines) and (lines[current_idx].startswith('-------') or 
                                       lines[current_idx].startswith('adapter')):
        current_idx += 1
    
    # Parse adapter lines
    while current_idx < len(lines):
        line = lines[current_idx].strip()
        
        if (line.startswith("VIRTUAL ADAPTERS") or line.startswith("+--") or 
            line.startswith("NO CONTROL CHANNEL") or line == ""):
            break
        
        if line and not line.startswith('-------'):
            parts = line.split()
            if len(parts) >= 3 and parts[0].startswith('ent'):
                adapter_name = parts[0]
                hardware_path = parts[2]
                real_adapters.append({
                    'adapter_name': adapter_name,
                    'hardware_path': hardware_path
                })
        
        current_idx += 1
    
    return real_adapters, current_idx

def parse_virtual_adapters_section(lines, start_idx):
    """Parse VIRTUAL ADAPTERS section."""
    virtual_adapters = []
    current_idx = start_idx + 1
    
    # Skip header lines
    while current_idx < len(lines) and (lines[current_idx].startswith('-------') or 
                                       lines[current_idx].startswith('adapter')):
        current_idx += 1
    
    # Parse adapter lines
    while current_idx < len(lines):
        line = lines[current_idx].strip()
        
        if (line.startswith("+--") or line.startswith("NO CONTROL CHANNEL") or line == ""):
            break
        
        if line and not line.startswith('-------'):
            parts = line.split()
            if len(parts) >= 3 and parts[0].startswith('ent'):
                adapter_name = parts[0]
                hardware_path = parts[2]
                virtual_adapters.append({
                    'adapter_name': adapter_name,
                    'hardware_path': hardware_path
                })
        
        current_idx += 1
    
    return virtual_adapters, current_idx

def extract_network_config_from_file(file_path):
    """Extract complete network configuration from a lssea log file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
        
        hostname = extract_hostname_from_file(file_path)
        
        sea_sections = []
        current_idx = 0
        
        while current_idx < len(lines):
            line = lines[current_idx].strip()
            if line.startswith("SEA :"):
                sea_data, current_idx = parse_sea_section(lines, current_idx)
                if sea_data:
                    sea_sections.append(sea_data)
            else:
                current_idx += 1
        
        return {
            'hostname': hostname,
            'sea_sections': sea_sections
        }
        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

def generate_text_diagram(config_data, output_path):
    """Generate a text-based diagram when PIL is not available."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("NETWORK CONFIGURATION DIAGRAM\n")
        f.write("=" * 50 + "\n\n")
        
        for config in config_data:
            hostname = config.get('hostname', 'Unknown')
            sea_sections = config.get('sea_sections', [])
            
            f.write(f"HOSTNAME: {hostname}\n")
            f.write("-" * 30 + "\n\n")
            
            for i, sea in enumerate(sea_sections):
                sea_name = sea.get('sea_name', 'Unknown SEA')
                f.write(f"SEA {i+1}: {sea_name}\n")
                
                # ETHERCHANNEL
                etherchannel = sea.get('etherchannel')
                if etherchannel and etherchannel.get('adapters'):
                    f.write(f"  └── ETHERCHANNEL: {', '.join(etherchannel['adapters'])}\n")
                
                # REAL ADAPTERS
                real_adapters = sea.get('real_adapters', [])
                if real_adapters:
                    f.write(f"  └── REAL ADAPTERS:\n")
                    for adapter in real_adapters:
                        f.write(f"      ├── {adapter['adapter_name']} ({adapter['hardware_path']})\n")
                
                # VIRTUAL ADAPTERS
                virtual_adapters = sea.get('virtual_adapters', [])
                if virtual_adapters:
                    f.write(f"  └── VIRTUAL ADAPTERS:\n")
                    for adapter in virtual_adapters:
                        f.write(f"      ├── {adapter['adapter_name']} ({adapter['hardware_path']})\n")
                
                f.write("\n")
    
    print(f"Text diagram saved to: {output_path}")

def generate_pil_diagram(config_data, output_path):
    """Generate a visual diagram using PIL."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        class NetworkDiagramGenerator:
            def __init__(self, config_data):
                self.config_data = config_data
                self.width = 1200
                self.height = 800
                self.margin = 50
                self.box_width = 200
                self.box_height = 60
                
                # Colors
                self.hostname_color = (70, 130, 180)
                self.sea_color = (255, 165, 0)
                self.etherchannel_color = (50, 205, 50)
                self.real_adapter_color = (255, 69, 0)
                self.virtual_adapter_color = (138, 43, 226)
                self.line_color = (0, 0, 0)
                self.text_color = (255, 255, 255)
                
            def create_diagram(self, output_path):
                img = Image.new('RGB', (self.width, self.height), (255, 255, 255))
                draw = ImageDraw.Draw(img)
                
                try:
                    font_large = ImageFont.truetype("arial.ttf", 16)
                    font_medium = ImageFont.truetype("arial.ttf", 12)
                    font_small = ImageFont.truetype("arial.ttf", 10)
                except:
                    font_large = ImageFont.load_default()
                    font_medium = ImageFont.load_default()
                    font_small = ImageFont.load_default()
                
                y_offset = self.margin
                
                for config in self.config_data:
                    hostname = config.get('hostname', 'Unknown')
                    sea_sections = config.get('sea_sections', [])
                    
                    # Draw hostname box
                    hostname_x = (self.width - self.box_width) // 2
                    hostname_y = y_offset
                    self.draw_box(draw, hostname_x, hostname_y, self.box_width, self.box_height, 
                                 self.hostname_color, hostname, font_large)
                    
                    y_offset += self.box_height + 50
                    
                    # Draw SEA sections
                    sea_count = len(sea_sections)
                    if sea_count > 0:
                        sea_spacing = (self.width - 2 * self.margin - self.box_width) // (sea_count + 1)
                        sea_start_x = self.margin + sea_spacing
                        
                        for i, sea in enumerate(sea_sections):
                            sea_x = sea_start_x + i * sea_spacing
                            sea_y = y_offset
                            
                            sea_name = sea.get('sea_name', 'Unknown SEA')
                            self.draw_box(draw, sea_x, sea_y, self.box_width, self.box_height, 
                                         self.sea_color, sea_name, font_medium)
                            
                            self.draw_sea_components(draw, sea, sea_x, sea_y, font_small)
                            
                            # Connect hostname to SEA
                            self.draw_line(draw, 
                                         hostname_x + self.box_width // 2, hostname_y + self.box_height,
                                         sea_x + self.box_width // 2, sea_y)
                        
                        y_offset += self.box_height + 200
                
                img.save(output_path)
                print(f"Visual diagram saved to: {output_path}")
            
            def draw_sea_components(self, draw, sea, sea_x, sea_y, font):
                components_y = sea_y + self.box_height + 20
                
                # ETHERCHANNEL
                etherchannel = sea.get('etherchannel')
                if etherchannel and etherchannel.get('adapters'):
                    etherchannel_x = sea_x - 50
                    etherchannel_y = components_y
                    adapter_names = ', '.join(etherchannel['adapters'])
                    self.draw_box(draw, etherchannel_x, etherchannel_y, self.box_width, self.box_height,
                                 self.etherchannel_color, f"EC: {adapter_names}", font)
                    
                    self.draw_line(draw, 
                                 sea_x + self.box_width // 2, sea_y + self.box_height,
                                 etherchannel_x + self.box_width // 2, etherchannel_y)
                    
                    components_y += self.box_height + 20
                
                # REAL ADAPTERS
                real_adapters = sea.get('real_adapters', [])
                if real_adapters:
                    real_adapters_x = sea_x - 50
                    real_adapters_y = components_y
                    
                    hw_paths = {}
                    for adapter in real_adapters:
                        hw_path = adapter.get('hardware_path', 'Unknown')
                        if hw_path not in hw_paths:
                            hw_paths[hw_path] = []
                        hw_paths[hw_path].append(adapter['adapter_name'])
                    
                    for hw_path, adapter_names in hw_paths.items():
                        adapter_text = f"RA: {', '.join(adapter_names)}"
                        self.draw_box(draw, real_adapters_x, real_adapters_y, self.box_width, self.box_height,
                                     self.real_adapter_color, adapter_text, font)
                        
                        if etherchannel and etherchannel.get('adapters'):
                            self.draw_line(draw,
                                         etherchannel_x + self.box_width // 2, etherchannel_y + self.box_height,
                                         real_adapters_x + self.box_width // 2, real_adapters_y)
                        else:
                            self.draw_line(draw,
                                         sea_x + self.box_width // 2, sea_y + self.box_height,
                                         real_adapters_x + self.box_width // 2, real_adapters_y)
                        
                        real_adapters_y += self.box_height + 10
                
                # VIRTUAL ADAPTERS
                virtual_adapters = sea.get('virtual_adapters', [])
                if virtual_adapters:
                    virtual_adapters_x = sea_x + 50
                    virtual_adapters_y = sea_y - self.box_height - 20
                    
                    hw_paths = {}
                    for adapter in virtual_adapters:
                        hw_path = adapter.get('hardware_path', 'Unknown')
                        if hw_path not in hw_paths:
                            hw_paths[hw_path] = []
                        hw_paths[hw_path].append(adapter['adapter_name'])
                    
                    for hw_path, adapter_names in hw_paths.items():
                        adapter_text = f"VA: {', '.join(adapter_names)}"
                        self.draw_box(draw, virtual_adapters_x, virtual_adapters_y, self.box_width, self.box_height,
                                     self.virtual_adapter_color, adapter_text, font)
                        
                        self.draw_line(draw,
                                     virtual_adapters_x + self.box_width // 2, virtual_adapters_y + self.box_height,
                                     sea_x + self.box_width // 2, sea_y)
                        
                        virtual_adapters_y -= self.box_height + 10
            
            def draw_box(self, draw, x, y, width, height, color, text, font):
                draw.rectangle([x, y, x + width, y + height], fill=color, outline=self.line_color, width=2)
                
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                text_x = x + (width - text_width) // 2
                text_y = y + (height - text_height) // 2
                
                draw.text((text_x, text_y), text, fill=self.text_color, font=font)
            
            def draw_line(self, draw, x1, y1, x2, y2):
                draw.line([x1, y1, x2, y2], fill=self.line_color, width=2)
        
        generator = NetworkDiagramGenerator(config_data)
        generator.create_diagram(output_path)
        
    except ImportError:
        print("PIL (Pillow) not available. Generating text diagram instead.")
        generate_text_diagram(config_data, output_path.replace('.png', '.txt'))

def main():
    """Main function to process all lssea*log files and generate diagrams."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "inputfile")
    
    if not os.path.exists(input_dir):
        print(f"Error: Directory '{input_dir}' does not exist.")
        return
    
    pattern = os.path.join(input_dir, "lssea*log")
    log_files = glob.glob(pattern)
    
    if not log_files:
        print(f"No lssea*log files found in '{input_dir}'")
        return
    
    print(f"Found {len(log_files)} lssea*log file(s):")
    print("-" * 50)
    
    all_configs = []
    
    for file_path in sorted(log_files):
        filename = os.path.basename(file_path)
        print(f"Processing: {filename}")
        
        config = extract_network_config_from_file(file_path)
        if config:
            all_configs.append(config)
            print(f"  Hostname: {config['hostname']}")
            print(f"  SEA sections found: {len(config['sea_sections'])}")
        else:
            print(f"  Failed to extract configuration")
        print()
    
    # Save to JSON file
    json_file = os.path.join(script_dir, "network_config.json")
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_configs, f, indent=2)
        print(f"Network configuration saved to: {json_file}")
    except Exception as e:
        print(f"Error saving configuration: {e}")
    
    # Generate diagram
    diagram_file = os.path.join(script_dir, "network_diagram.png")
    generate_pil_diagram(all_configs, diagram_file)

if __name__ == "__main__":
    main() 