#!/usr/bin/env python3
"""
Comprehensive script to extract network configuration from lssea*log files
and generate a network diagram.
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
    """
    Parse a SEA section starting from the given index.
    Returns the parsed data and the next index to continue parsing.
    """
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
        
        # Stop if we hit another section or empty line
        if line.startswith("SEA :") or line.startswith("+--") or line == "":
            break
            
        # Parse property lines
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
        
        # Stop if we hit another section
        if (line.startswith("REAL ADAPTERS") or line.startswith("VIRTUAL ADAPTERS") or 
            line.startswith("+--") or line == ""):
            break
        
        # Parse adapter line
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
        
        # Stop if we hit another section
        if (line.startswith("VIRTUAL ADAPTERS") or line.startswith("+--") or 
            line.startswith("NO CONTROL CHANNEL") or line == ""):
            break
        
        # Parse adapter line
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
        
        # Stop if we hit another section
        if (line.startswith("+--") or line.startswith("NO CONTROL CHANNEL") or line == ""):
            break
        
        # Parse adapter line
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
        
        # Extract hostname
        hostname = extract_hostname_from_file(file_path)
        
        # Find all SEA sections
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

def main():
    """Main function to process all lssea*log files and extract network configuration."""
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
    output_file = os.path.join(script_dir, "network_config.json")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_configs, f, indent=2)
        print(f"Network configuration saved to: {output_file}")
    except Exception as e:
        print(f"Error saving configuration: {e}")
    
    return all_configs

if __name__ == "__main__":
    main() 