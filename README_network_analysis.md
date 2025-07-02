# Network Configuration Analysis and Diagram Generation

This directory contains Python scripts to extract network configuration from `lssea*log` files and generate visual network diagrams.

## Overview

The scripts extract the following information from lssea log files:
1. **Hostname** - The VIOS hostname
2. **SEA (Shared Ethernet Adapter)** - Device names and properties
3. **Etherchannel** - Adapter names if present
4. **Real Adapters** - Physical adapter names and hardware paths
5. **Virtual Adapters** - Virtual adapter names and hardware paths

## Files

### Core Scripts
- `extract_network_config_fixed.py` - Main extraction script (recommended)
- `generate_diagram.py` - Diagram generation script
- `network_analyzer.py` - Combined extraction and diagram generation

### Legacy Scripts
- `extract_network_config.py` - Original extraction script (has parsing issues)
- `generate_network_diagram.py` - Original diagram script

### Output Files
- `network_config_fixed.json` - Extracted configuration data
- `network_diagram.png` - Generated network diagram
- `network_config.json` - Original extraction output (has issues)

## Usage

### Step 1: Extract Network Configuration
```bash
python extract_network_config_fixed.py
```

This will:
- Process all `lssea*log` files in the `inputfile` directory
- Extract hostname, SEA sections, etherchannels, and adapters
- Save the configuration to `network_config_fixed.json`
- Display a summary of what was found

### Step 2: Generate Network Diagram
```bash
python generate_diagram.py
```

This will:
- Read the configuration from `network_config_fixed.json`
- Generate a visual diagram showing the network topology
- Save the diagram as `network_diagram.png`

### Alternative: Combined Script
```bash
python network_analyzer.py
```

This combines both extraction and diagram generation in one script.

## Diagram Layout

The generated diagram shows:

1. **Hostname** - Large blue rectangle at the top
2. **SEA Devices** - Orange rectangles below the hostname
3. **Etherchannel** - Green rectangles (if present) below SEA
4. **Real Adapters** - Red rectangles below SEA/etherchannel
5. **Virtual Adapters** - Purple rectangles above SEA

### Color Coding
- 🔵 **Blue** - Hostname
- 🟠 **Orange** - SEA (Shared Ethernet Adapter)
- 🟢 **Green** - Etherchannel
- 🔴 **Red** - Real (Physical) Adapters
- 🟣 **Purple** - Virtual Adapters

## Example Output

```
Found 1 lssea*log file(s):
--------------------------------------------------
Processing: lssea_P10VIOF041A.log
  Hostname: P10VIOF041A
  SEA sections found: 6
    SEA 1: ent29
      ETHERCHANNEL: ['ent16']
      REAL ADAPTERS: 4
      VIRTUAL ADAPTERS: 4
    SEA 2: ent30
      REAL ADAPTERS: 1
      VIRTUAL ADAPTERS: 1
    ...
Network configuration saved to: network_config_fixed.json
Network diagram saved to: network_diagram.png
```

## JSON Structure

The extracted configuration is saved in JSON format:

```json
[
  {
    "hostname": "P10VIOF041A",
    "sea_sections": [
      {
        "sea_name": "ent29",
        "properties": {
          "ha_mode": "Sharing",
          "state": "PRIMARY_SH",
          "number of adapters": "5",
          "priority": "1",
          "vlans": "11 12 13 14 101 102..."
        },
        "etherchannel": {
          "adapters": ["ent16"]
        },
        "real_adapters": [
          {
            "adapter_name": "ent0",
            "hardware_path": "U5B61.001.WZS02T0-P0-C2-T0"
          }
        ],
        "virtual_adapters": [
          {
            "adapter_name": "ent18",
            "hardware_path": "U9080.HEX.78C01A8-V1-C11-T0"
          }
        ]
      }
    ]
  }
]
```

## Requirements

- Python 3.x
- Pillow (PIL) for diagram generation: `pip install Pillow`

## Troubleshooting

### Common Issues

1. **No lssea*log files found**
   - Ensure log files are in the `inputfile` directory
   - Check file naming pattern (must start with "lssea" and end with ".log")

2. **PIL/Pillow not available**
   - Install with: `pip install Pillow`
   - The script will fall back to text output if PIL is not available

3. **Parsing issues**
   - Use `extract_network_config_fixed.py` instead of the original script
   - The fixed version handles ANSI escape characters better

4. **Diagram too crowded**
   - The script automatically limits text in boxes to prevent overflow
   - For complex configurations, the diagram may be dense but readable

## File Structure

```
hmcscannerdraw/
├── inputfile/
│   └── lssea_P10VIOF041A.log
├── extract_network_config_fixed.py
├── generate_diagram.py
├── network_analyzer.py
├── network_config_fixed.json
├── network_diagram.png
└── README_network_analysis.md
```

## Advanced Usage

### Customizing the Diagram

You can modify `generate_diagram.py` to:
- Change colors by modifying the color tuples
- Adjust layout by changing width, height, and spacing values
- Modify font sizes for different text elements
- Add additional information to the diagram

### Processing Multiple Files

The scripts automatically process all `lssea*log` files in the input directory. Each file will be processed separately and the results combined in the output.

### Extending the Parser

To extract additional information, modify the parsing functions in `extract_network_config_fixed.py`:
- `parse_sea_section()` - For SEA properties
- `parse_etherchannel_section()` - For etherchannel details
- `parse_real_adapters_section()` - For real adapter information
- `parse_virtual_adapters_section()` - For virtual adapter information 