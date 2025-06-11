# NetFlux5G Editor - Testing Templates

This directory contains pre-configured topology templates for testing the NetFlux5G Editor application with various 5G network scenarios.

## Available Templates

### 1. Simple 5G Standalone Network (`topology_simple_5g.json`)
- **Purpose**: Basic 5G SA testing
- **Components**: 1 AMF, 1 UPF, 1 gNB, 2 UEs
- **Use Case**: Learning and basic functionality testing
- **Network**: Single DNN (internet)

### 2. Multi-UPF 5G Network (`topology_multi_upf_5g.json`)
- **Purpose**: Advanced 5G network with multiple UPFs
- **Components**: 1 AMF, 1 SMF, 2 UPFs, 2 gNBs, 4 UEs
- **Use Case**: Testing multiple DNNs and network slicing
- **Networks**: 
  - Campus: internet, internet2 DNNs
  - Enterprise: web1, web2 DNNs

### 3. Hybrid WiFi-5G Network (`topology_hybrid_wifi_5g.json`)
- **Purpose**: Mixed WiFi and 5G deployment
- **Components**: 1 AMF, 1 UPF, 1 gNB, 2 APs, 2 UEs, 4 STAs, 2 Hosts
- **Use Case**: Testing heterogeneous networks
- **Features**: WiFi and 5G coexistence

## Docker Compose Testing Environment

### Setup Instructions

1. **Start the 5G Core Network**:
   ```bash
   cd 5g-configs
   docker-compose -f docker-compose-test.yml up -d
   ```

2. **Verify Services**:
   ```bash
   docker-compose -f docker-compose-test.yml ps
   ```

3. **Access Web UI**:
   - URL: http://localhost:3000
   - Default credentials: admin/1423

4. **Add Test Subscribers**:
   - IMSI: 999700000000001
   - Key: 465B5CE8B199B49FAA5F0A2EE238A6BC
   - OPc: E8ED289DEBA952E4283B54E88E6183CA

### Loading Templates in NetFlux5G Editor

1. **Open the application**
2. **File → Load Topology**
3. **Select one of the JSON templates**
4. **Customize as needed**
5. **Export to Mininet script**

### Testing Workflow

1. **Load Template**: Import JSON topology
2. **Modify Properties**: Adjust component configurations
3. **Export Script**: Generate Mininet Python script
4. **Run Network**: Execute in Mininet-WiFi environment
5. **Test Connectivity**: Verify 5G and WiFi connections

## Configuration Files

Each template uses the following configuration files:
- `amf.yaml` - AMF configuration
- `smf.yaml` - SMF configuration  
- `upf.yaml` - UPF for internet/internet2 DNNs
- `upf2.yaml` - UPF for web1/web2 DNNs
- `*.yaml` - Other 5G core function configs

## Network Parameters

### Default MCC/MNC
- MCC: 999 (Test network)
- MNC: 70 (Test operator)

### IP Ranges
- UE Network 1: 10.100.0.0/16 (internet DNN)
- UE Network 2: 10.200.0.0/16 (internet2 DNN)
- UE Network 3: 10.51.0.0/16 (web1 DNN)
- UE Network 4: 10.52.0.0/16 (web2 DNN)

### Ports
- AMF NGAP: 38412
- Web UI: 3000
- NRF SBI: 7777

## Troubleshooting

### Common Issues

1. **Container startup fails**:
   ```bash
   docker-compose -f docker-compose-test.yml logs [service_name]
   ```

2. **UE registration fails**:
   - Check IMSI is registered in Web UI
   - Verify AMF/gNB connectivity
   - Check configuration parameters match

3. **Export fails**:
   - Ensure all required properties are set
   - Verify component names are unique
   - Check for missing links

### Logs and Debugging

- **Container logs**: `docker logs [container_name]`
- **5GC logs**: Located in `/opt/open5gs/var/log/open5gs/`
- **Network status**: Use `docker network ls` and `docker network inspect`

## Advanced Testing

### Custom Scenarios

1. **Network Slicing**: Modify S-NSSAI values in templates
2. **QoS Testing**: Configure different QCI values
3. **Handover**: Add multiple gNBs with overlapping coverage
4. **Load Testing**: Scale UE numbers in templates

### Integration Testing

1. **Export topology** from NetFlux5G Editor
2. **Run Mininet-WiFi** script with containernet
3. **Verify 5G registration** via logs
4. **Test data connectivity** between UEs and internet

This testing framework provides comprehensive scenarios for validating NetFlux5G Editor functionality across different network topologies and use cases.
