# NetFlux5G Editor

A graphical topology editor for designing and deploying 5G network infrastructures with integration for Mininet and Docker Compose.

## Features

- **Visual Topology Design**: Drag-and-drop interface for creating network topologies
- **5G Component Support**: UE, gNB, UPF, AMF, SMF, NRF, SCP, and other 5G core components
- **Multi-Platform Export**: Generate Mininet scripts and Docker Compose configurations
- **Automated Deployment**: One-click deployment with RunAll functionality
- **Component Properties**: Configurable properties for each network element
- **Link Management**: Visual link creation between network components

## Supported Components

### 5G Core Network
- **AMF** (Access and Mobility Management Function)
- **SMF** (Session Management Function)
- **UPF** (User Plane Function)
- **NRF** (Network Repository Function)
- **SCP** (Service Communication Proxy)
- **AUSF** (Authentication Server Function)
- **UDM** (Unified Data Management)
- **UDR** (Unified Data Repository)
- **PCF** (Policy Control Function)
- **BSF** (Binding Support Function)
- **NSSF** (Network Slice Selection Function)

### Network Elements
- **UE** (User Equipment)
- **gNB** (5G Base Station)
- **Host** (Generic network host)
- **STA** (Station)
- **AP** (Access Point)
- **Controller** (SDN Controller)
- **Docker Host** (Containerized host)

## Installation

### Prerequisites

- Python 3.7+
- PyQt5
- Docker (for container deployment)
- Mininet (for network emulation, Linux only)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install System Dependencies (Ubuntu/Debian)

```bash
# For Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose

# For Mininet (Linux only)
sudo apt-get install mininet

# For PyQt5 system dependencies
sudo apt-get install python3-pyqt5
```

## Usage

### Starting the Application

```bash
cd netflux5g-editor/src
python main.py
```

### Creating a Topology

1. **Add Components**: Drag components from the toolbar to the canvas
2. **Configure Properties**: Right-click components to set properties
3. **Create Links**: Use the Link tool to connect components
4. **Export**: Use File menu to export to Mininet or Docker Compose

### Automated Deployment

1. **Design Topology**: Create your 5G network topology
2. **Configure Components**: Set properties for 5G core components
3. **Run All**: Click the RunAll button for automated deployment
4. **Monitor**: Use the built-in status monitoring

## Export Formats

### Mininet Script Export
- Generates Python scripts for Mininet network emulation
- Supports wireless components (AP, STA, UE, gNB)
- Configurable host properties and links

### Docker Compose Export  
- Creates docker-compose.yaml for 5G core deployment
- Includes configuration files for Open5GS components
- Automated container orchestration

## Configuration

### 5G Core Configuration
The application includes pre-configured YAML files for:
- AMF, SMF, UPF, NRF, SCP
- AUSF, UDM, UDR, PCF, BSF, NSSF
- Custom configuration via component properties

### Network Simulation
- Configurable IP addressing
- Wireless range and mobility parameters
- QoS and traffic shaping options

## File Structure

```
netflux5g-editor/
├── src/
│   ├── main.py                 # Application entry point
│   └── gui/
│       ├── canvas.py           # Main drawing canvas
│       ├── components.py       # Network component classes
│       ├── links.py           # Link management
│       ├── toolbar.py         # UI toolbar
│       ├── mininet_export.py  # Mininet script generation
│       ├── compose_export.py  # Docker Compose export
│       ├── automation_runner.py # RunAll functionality
│       ├── widgets/
│       │   └── Dialog.py      # Property dialog widgets
│       ├── ui/                # UI definition files
│       └── 5g-configs/        # 5G configuration templates
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with PyQt5 for the GUI framework
- Integrates with Open5GS for 5G core network components
- Uses Mininet for network emulation capabilities
- Docker integration for containerized deployment

## Troubleshooting

### Common Issues

**PyQt5 Import Errors**
```bash
pip install --upgrade PyQt5
```

**Docker Permission Issues**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

**Mininet Requires Root**
```bash
sudo python main.py  # When using Mininet features
```

### Support

For issues and questions:
1. Check the troubleshooting section above
2. Review existing GitHub issues
3. Create a new issue with detailed information

## Roadmap

- [ ] Enhanced 5G slice management
- [ ] Real-time network monitoring
- [ ] Advanced QoS configuration
- [ ] Integration with additional simulators
- [ ] Web-based interface option
