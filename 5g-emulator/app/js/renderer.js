const { ipcRenderer } = require('electron');
const axios = require('axios');

// Initialize bootstrap modals
const addUeModal = new bootstrap.Modal(document.getElementById('addUeModal'));
const addGnbModal = new bootstrap.Modal(document.getElementById('addGnbModal'));
const flowRulesModal = new bootstrap.Modal(document.getElementById('flowRulesModal'));

// Initialize cytoscape for network topology
let cy = cytoscape({
  container: document.getElementById('topology-container'),
  style: [
    {
      selector: 'node',
      style: {
        'background-color': '#666',
        'label': 'data(label)',
        'text-valign': 'center',
        'color': '#fff',
        'text-outline-width': 2,
        'text-outline-color': '#666',
        'font-size': '12px'
      }
    },
    {
      selector: 'node[type="core"]',
      style: {
        'background-color': '#007bff',
        'shape': 'rectangle',
        'text-outline-color': '#007bff'
      }
    },
    {
      selector: 'node[type="ran"]',
      style: {
        'background-color': '#28a745',
        'shape': 'hexagon',
        'text-outline-color': '#28a745'
      }
    },
    {
      selector: 'node[type="ue"]',
      style: {
        'background-color': '#fd7e14',
        'shape': 'ellipse',
        'text-outline-color': '#fd7e14'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 3,
        'line-color': '#ccc',
        'target-arrow-color': '#ccc',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier'
      }
    },
    {
      selector: 'edge[type="data"]',
      style: {
        'line-color': '#dc3545',
        'target-arrow-color': '#dc3545',
        'line-style': 'dashed'
      }
    }
  ],
  layout: {
    name: 'grid',
    rows: 3
  },
  userZoomingEnabled: true,
  userPanningEnabled: true,
  boxSelectionEnabled: true
});

// Sample topology for initial display
function initializeTopology() {
  cy.add([
    // Core Network Nodes
    { data: { id: 'nrf', label: 'NRF', type: 'core' } },
    { data: { id: 'amf', label: 'AMF', type: 'core' } },
    { data: { id: 'smf', label: 'SMF', type: 'core' } },
    { data: { id: 'upf', label: 'UPF', type: 'core' } },

    // RAN Nodes
    { data: { id: 'gnb', label: 'gNB', type: 'ran' } },

    // UE Nodes
    { data: { id: 'ue', label: 'UE', type: 'ue' } },

    // Connections
    { data: { id: 'nrf-amf', source: 'nrf', target: 'amf' } },
    { data: { id: 'nrf-smf', source: 'nrf', target: 'smf' } },
    { data: { id: 'amf-smf', source: 'amf', target: 'smf' } },
    { data: { id: 'smf-upf', source: 'smf', target: 'upf' } },
    { data: { id: 'amf-gnb', source: 'amf', target: 'gnb' } },
    { data: { id: 'gnb-ue', source: 'gnb', target: 'ue' } }
  ]);

  cy.layout({ name: 'grid', rows: 3 }).run();
}

// Variables for application state
let dockerStatus = 'unknown';
let selectedComponent = null;
let trafficEvents = [];
let components = {
  core: ['nrf', 'amf', 'smf', 'upf'],
  ran: ['gnb'],
  ue: ['ue']
};

// UI elements
const viewSections = [
  'view-topology',
  'view-components',
  'view-traffic',
  'view-logs'
];

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
  // Initialize topology
  initializeTopology();

  // Check docker status
  ipcRenderer.send('check-docker-status');

  // Initialize component list
  updateComponentList();

  // Set up event listeners for navigation
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (event) => {
      const targetId = event.target.id.replace('nav-', 'view-');
      switchView(targetId);
    });
  });

  // Set up event listeners for Docker control
  document.getElementById('btn-docker-start').addEventListener('click', startDocker);
  document.getElementById('btn-docker-stop').addEventListener('click', stopDocker);

  // Set up event listeners for layout controls
  document.getElementById('btn-layout-circle').addEventListener('click', () => {
    cy.layout({ name: 'circle' }).run();
  });

  document.getElementById('btn-layout-grid').addEventListener('click', () => {
    cy.layout({ name: 'grid', rows: 3 }).run();
  });

  document.getElementById('btn-reset-view').addEventListener('click', () => {
    cy.fit();
    cy.center();
  });

  // Set up event listeners for sidebar actions
  document.getElementById('btn-add-ue').addEventListener('click', () => {
    // Populate gNB dropdown
    const gnbSelect = document.getElementById('ue-gnb');
    gnbSelect.innerHTML = '';
    components.ran.forEach(gnb => {
      const option = document.createElement('option');
      option.value = gnb;
      option.text = gnb;
      gnbSelect.appendChild(option);
    });

    addUeModal.show();
  });

  document.getElementById('btn-add-gnb').addEventListener('click', () => {
    addGnbModal.show();
  });

  document.getElementById('btn-sdn-flows').addEventListener('click', showFlowRules);
  document.getElementById('btn-sdn-stats').addEventListener('click', getSDNStats);

  document.getElementById('btn-confirm-add-ue').addEventListener('click', addNewUE);
  document.getElementById('btn-confirm-add-gnb').addEventListener('click', addNewGNB);
  document.getElementById('btn-clear-logs').addEventListener('click', clearLogs);

  // Set up event listener for traffic generation
  document.getElementById('traffic-form').addEventListener('submit', (event) => {
    event.preventDefault();
    generateTraffic();
  });

  // Setup component selection
  document.getElementById('component-list').addEventListener('click', (event) => {
    if (event.target.classList.contains('list-group-item')) {
      selectComponent(event.target.dataset.id);
    }
  });

  // Setup component actions
  document.getElementById('btn-restart-component').addEventListener('click', restartComponent);
  document.getElementById('btn-remove-component').addEventListener('click', removeComponent);

// Set up periodic status updates (every 5 seconds)
  setInterval(updateNetworkStatus, 5000);

  // Initialize network status
  updateNetworkStatus();
});

// Docker control functions
function startDocker() {
  document.getElementById('docker-status-indicator').textContent = 'Starting...';
  document.getElementById('docker-status-indicator').className = 'badge bg-warning me-2';
  ipcRenderer.send('start-docker-compose');
}

function stopDocker() {
  document.getElementById('docker-status-indicator').textContent = 'Stopping...';
  document.getElementById('docker-status-indicator').className = 'badge bg-warning me-2';
  ipcRenderer.send('stop-docker-compose');
}

// View switching function
function switchView(targetId) {
  // Hide all views
  viewSections.forEach(section => {
    document.getElementById(section).classList.add('d-none');
  });

  // Show selected view
  document.getElementById(targetId).classList.remove('d-none');

  // Update navigation links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
  });

  const navId = targetId.replace('view-', 'nav-');
  document.getElementById(navId).classList.add('active');
}

// Component management functions
function updateComponentList() {
  const list = document.getElementById('component-list');
  list.innerHTML = '';

  // Core components
  const coreHeader = document.createElement('div');
  coreHeader.className = 'list-group-item list-group-item-secondary';
  coreHeader.textContent = 'Core Network';
  list.appendChild(coreHeader);

  components.core.forEach(component => {
    const item = document.createElement('a');
    item.href = '#';
    item.className = 'list-group-item list-group-item-action';
    item.dataset.id = component;
    item.textContent = component.toUpperCase();
    list.appendChild(item);
  });

  // RAN components
  const ranHeader = document.createElement('div');
  ranHeader.className = 'list-group-item list-group-item-secondary';
  ranHeader.textContent = 'Radio Access Network';
  list.appendChild(ranHeader);

  components.ran.forEach(component => {
    const item = document.createElement('a');
    item.href = '#';
    item.className = 'list-group-item list-group-item-action';
    item.dataset.id = component;
    item.textContent = component;
    list.appendChild(item);
  });

  // UE components
  const ueHeader = document.createElement('div');
  ueHeader.className = 'list-group-item list-group-item-secondary';
  ueHeader.textContent = 'User Equipment';
  list.appendChild(ueHeader);

  components.ue.forEach(component => {
    const item = document.createElement('a');
    item.href = '#';
    item.className = 'list-group-item list-group-item-action';
    item.dataset.id = component;
    item.textContent = component;
    list.appendChild(item);
  });

  // Also update traffic simulation dropdowns
  updateTrafficDropdowns();
}

function selectComponent(componentId) {
  selectedComponent = componentId;

  // Update UI to show selected component
  document.querySelectorAll('#component-list .list-group-item-action').forEach(item => {
    item.classList.remove('active');
  });

  const selectedItem = document.querySelector(`#component-list [data-id="${componentId}"]`);
  if (selectedItem) {
    selectedItem.classList.add('active');
  }

  // Fetch and display component details
  fetchComponentDetails(componentId);
}

function fetchComponentDetails(componentId) {
  const detailsContainer = document.getElementById('component-details');

  // First set loading state
  detailsContainer.innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';

  // In a real app, you would fetch this data from your Docker containers
  // Here we'll simulate it with a timeout
  setTimeout(() => {
    // Check if Docker is running
    if (dockerStatus !== 'running') {
      detailsContainer.innerHTML = '<div class="alert alert-warning">Docker is not running. Start the network to view component details.</div>';
      return;
    }

    // Simulate component details based on component type
    let content = '';

    if (components.core.includes(componentId)) {
      content = `
        <h5>${componentId.toUpperCase()}</h5>
        <p><strong>Type:</strong> Core Network Component</p>
        <p><strong>Status:</strong> <span class="badge bg-success">Running</span></p>
        <p><strong>Container ID:</strong> ${generateMockContainerId()}</p>
        <p><strong>IP Address:</strong> 172.17.0.${Math.floor(Math.random() * 10) + 2}</p>
        <p><strong>CPU Usage:</strong> ${Math.floor(Math.random() * 20)}%</p>
        <p><strong>Memory Usage:</strong> ${Math.floor(Math.random() * 200) + 50}MB</p>
        <p><strong>Connected Components:</strong> ${getConnectedComponents(componentId).join(', ')}</p>
      `;
    } else if (components.ran.includes(componentId)) {
      content = `
        <h5>${componentId}</h5>
        <p><strong>Type:</strong> Radio Access Network</p>
        <p><strong>Status:</strong> <span class="badge bg-success">Running</span></p>
        <p><strong>Container ID:</strong> ${generateMockContainerId()}</p>
        <p><strong>IP Address:</strong> 172.17.0.${Math.floor(Math.random() * 10) + 12}</p>
        <p><strong>CPU Usage:</strong> ${Math.floor(Math.random() * 20)}%</p>
        <p><strong>Memory Usage:</strong> ${Math.floor(Math.random() * 200) + 50}MB</p>
        <p><strong>Connected UEs:</strong> ${components.ue.length}</p>
        <p><strong>Signal Strength:</strong> -${Math.floor(Math.random() * 50) + 70}dBm</p>
      `;
    } else if (components.ue.includes(componentId)) {
      content = `
        <h5>${componentId}</h5>
        <p><strong>Type:</strong> User Equipment</p>
        <p><strong>Status:</strong> <span class="badge bg-success">Connected</span></p>
        <p><strong>IMSI:</strong> 00101000000001</p>
        <p><strong>IP Address:</strong> 10.45.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 254)}</p>
        <p><strong>Connected to:</strong> ${components.ran[0]}</p>
        <p><strong>Signal Strength:</strong> -${Math.floor(Math.random() * 30) + 70}dBm</p>
        <p><strong>Data Usage:</strong> ${(Math.random() * 10).toFixed(2)}MB</p>
      `;
    }

    detailsContainer.innerHTML = content;
  }, 500);
}

function getConnectedComponents(componentId) {
  // Return mock connected components based on our topology
  const connections = {
    'nrf': ['amf', 'smf'],
    'amf': ['nrf', 'smf', 'gnb'],
    'smf': ['nrf', 'amf', 'upf'],
    'upf': ['smf'],
    'gnb': ['amf', 'ue'],
    'ue': ['gnb']
  };

  return connections[componentId] || [];
}

function generateMockContainerId() {
  // Generate a random mock Docker container ID
  const chars = 'abcdef0123456789';
  let result = '';
  for (let i = 0; i < 12; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

// Network management functions
function addNewUE() {
  const imsi = document.getElementById('ue-imsi').value;
  const gnb = document.getElementById('ue-gnb').value;

  if (!imsi || !gnb) {
    alert('Please fill in all fields');
    return;
  }

  // Generate a unique ID for the new UE
  const ueId = `ue-${components.ue.length + 1}`;

  // In a real app, this would create a new Docker container
  // Here we'll just update our UI
  components.ue.push(ueId);

  // Add to the topology
  cy.add([
    { data: { id: ueId, label: ueId, type: 'ue' } },
    { data: { id: `${gnb}-${ueId}`, source: gnb, target: ueId } }
  ]);

  // Update UI
  updateComponentList();

  // Add a traffic event
  addTrafficEvent({
    type: 'connection',
    source: ueId,
    target: gnb,
    timestamp: new Date().toISOString(),
    details: `New UE ${ueId} connected to ${gnb}`
  });

  // Close the modal
  addUeModal.hide();

  // Update the layout
  cy.layout({ name: 'grid' }).run();
}

function addNewGNB() {
  const gnbId = document.getElementById('gnb-id').value;
  const location = document.getElementById('gnb-location').value;

  if (!gnbId || !location) {
    alert('Please fill in all fields');
    return;
  }

  // In a real app, this would create a new Docker container
  // Here we'll just update our UI
  components.ran.push(gnbId);

  // Add to the topology
  cy.add([
    { data: { id: gnbId, label: gnbId, type: 'ran' } },
    { data: { id: `amf-${gnbId}`, source: 'amf', target: gnbId } }
  ]);

  // Update UI
  updateComponentList();

  // Add a traffic event
  addTrafficEvent({
    type: 'network',
    source: 'amf',
    target: gnbId,
    timestamp: new Date().toISOString(),
    details: `New gNB ${gnbId} added at ${location}`
  });

  // Close the modal
  addGnbModal.hide();

  // Update the layout
  cy.layout({ name: 'grid' }).run();
}

function restartComponent() {
  if (!selectedComponent) {
    alert('Please select a component first');
    return;
  }

  // In a real app, this would restart the Docker container
  // Here we'll just simulate it

  // Add to logs
  const logElement = document.getElementById('docker-logs');
  logElement.innerHTML += `[${new Date().toLocaleTimeString()}] Restarting component: ${selectedComponent}\n`;
  logElement.scrollTop = logElement.scrollHeight;

  // Add a traffic event
  addTrafficEvent({
    type: 'management',
    source: 'system',
    target: selectedComponent,
    timestamp: new Date().toISOString(),
    details: `Component ${selectedComponent} restarted`
  });
}

function removeComponent() {
  if (!selectedComponent) {
    alert('Please select a component first');
    return;
  }

  // Don't allow removing core components
  if (components.core.includes(selectedComponent)) {
    alert('Cannot remove core network components');
    return;
  }

  // In a real app, this would remove the Docker container
  // Here we'll just update our UI

  // Remove from components list
  if (components.ran.includes(selectedComponent)) {
    components.ran = components.ran.filter(c => c !== selectedComponent);
  } else if (components.ue.includes(selectedComponent)) {
    components.ue = components.ue.filter(c => c !== selectedComponent);
  }

  // Remove from topology
  cy.remove(`#${selectedComponent}`);

  // Update UI
  updateComponentList();
  selectedComponent = null;
  document.getElementById('component-details').innerHTML = '<p class="text-muted">Select a component to view details</p>';

  // Add to logs
  const logElement = document.getElementById('docker-logs');
  logElement.innerHTML += `[${new Date().toLocaleTimeString()}] Removed component: ${selectedComponent}\n`;
  logElement.scrollTop = logElement.scrollHeight;
}

// Traffic simulation functions
function updateTrafficDropdowns() {
  const sourceSelect = document.getElementById('traffic-source');
  const targetSelect = document.getElementById('traffic-target');

  // Clear current options
  sourceSelect.innerHTML = '';
  targetSelect.innerHTML = '';

  // Add UEs as sources
  components.ue.forEach(ue => {
    const option = document.createElement('option');
    option.value = ue;
    option.text = ue;
    sourceSelect.appendChild(option);
  });

  // Add Core components as targets
  components.core.forEach(component => {
    const option = document.createElement('option');
    option.value = component;
    option.text = component.toUpperCase();
    targetSelect.appendChild(option);
  });
}

function generateTraffic() {
  const source = document.getElementById('traffic-source').value;
  const target = document.getElementById('traffic-target').value;
  const type = document.getElementById('traffic-type').value;
  const size = parseInt(document.getElementById('traffic-size').value);

  if (!source || !target) {
    alert('Please select source and target');
    return;
  }

  // In a real app, this would trigger traffic in the Docker containers
  // Here we'll just simulate it by adding a visual edge and a traffic event

  // Create a unique ID for this traffic flow
  const flowId = `flow-${Date.now()}`;

  // Add a temporary edge to visualize the traffic
  cy.add([
    { 
      data: { 
        id: flowId, 
        source: source, 
        target: target, 
        type: 'data'
      }
    }
  ]);

  // Add a traffic event
  addTrafficEvent({
    type: type,
    source: source,
    target: target,
    size: size,
    timestamp: new Date().toISOString(),
    details: `${type.toUpperCase()} traffic from ${source} to ${target} (${size} KB)`
  });

  // Remove the edge after a delay
  setTimeout(() => {
    cy.remove(`#${flowId}`);
  }, 3000);
}

function addTrafficEvent(event) {
  // Add event to our array
  trafficEvents.unshift(event);

  // Keep only the last 20 events
  if (trafficEvents.length > 20) {
    trafficEvents.pop();
  }

  // Update the UI
  updateTrafficEvents();
}

function updateTrafficEvents() {
  const container = document.getElementById('traffic-events');
  container.innerHTML = '';

  trafficEvents.forEach(event => {
    const time = new Date(event.timestamp).toLocaleTimeString();
    const item = document.createElement('li');
    item.className = 'list-group-item';

    let badgeClass = 'bg-secondary';
    if (event.type === 'http') badgeClass = 'bg-primary';
    if (event.type === 'video') badgeClass = 'bg-success';
    if (event.type === 'voip') badgeClass = 'bg-info';
    if (event.type === 'file') badgeClass = 'bg-warning';
    if (event.type === 'connection') badgeClass = 'bg-success';
    if (event.type === 'network') badgeClass = 'bg-info';
    if (event.type === 'management') badgeClass = 'bg-warning';

    item.innerHTML = `
      <div class="d-flex justify-content-between">
        <span><span class="badge ${badgeClass}">${event.type}</span> ${event.details}</span>
        <small class="text-muted">${time}</small>
      </div>
    `;

    container.appendChild(item);
  });
}

// SDN controller functions
function showFlowRules() {
  // In a real app, this would fetch actual flow rules from the SDN controller
  // Here we'll just show some mock data
  const flowRulesContent = document.getElementById('flow-rules-content');

  flowRulesContent.textContent = JSON.stringify([
    {
      "dpid": 1,
      "table_id": 0,
      "priority": 100,
      "match": {
        "in_port": 1,
        "eth_dst": "00:00:00:00:00:01"
      },
      "actions": [
        {
          "type": "OUTPUT",
          "port": 2
        }
      ]
    },
    {
      "dpid": 1,
      "table_id": 0,
      "priority": 100,
      "match": {
        "in_port": 2,
        "eth_dst": "00:00:00:00:00:02"
      },
      "actions": [
        {
          "type": "OUTPUT",
          "port": 1
        }
      ]
    }
  ], null, 2);

  flowRulesModal.show();
}

function getSDNStats() {
  // In a real app, this would fetch actual stats from the SDN controller
  // Here we'll just show some mock data in an alert
  const mockStats = {
    "switches": 1,
    "flows": 12,
    "packets_processed": 1542,
    "bytes_processed": 129528,
    "active_connections": 4
  };

  alert(`SDN Controller Stats:\n${JSON.stringify(mockStats, null, 2)}`);

  // Update badge
  document.getElementById('sdn-status').textContent = 'Active';
  document.getElementById('sdn-status').className = 'badge bg-success';
}

// Log management
function clearLogs() {
  document.getElementById('docker-logs').innerHTML = '';
}

// Status update functions
function updateNetworkStatus() {
  // In a real app, this would fetch actual status from your Docker containers
  // Here we'll just update the UI with mock data

  if (dockerStatus === 'running') {
    document.getElementById('core-status').textContent = 'Running';
    document.getElementById('core-status').className = 'badge bg-success';

    document.getElementById('ran-status').textContent = 'Running';
    document.getElementById('ran-status').className = 'badge bg-success';

    document.getElementById('ue-count').textContent = components.ue.length;
    document.getElementById('flow-count').textContent = Math.floor(Math.random() * 10) + components.ue.length;

    document.getElementById('sdn-status').textContent = 'Active';
    document.getElementById('sdn-status').className = 'badge bg-success';
  } else {
    document.getElementById('core-status').textContent = 'Stopped';
    document.getElementById('core-status').className = 'badge bg-secondary';

    document.getElementById('ran-status').textContent = 'Stopped';
    document.getElementById('ran-status').className = 'badge bg-secondary';

    document.getElementById('ue-count').textContent = '0';
    document.getElementById('flow-count').textContent = '0';

    document.getElementById('sdn-status').textContent = 'Inactive';
    document.getElementById('sdn-status').className = 'badge bg-secondary';
  }
}

// IPC event handlers for Docker communication
ipcRenderer.on('docker-output', (event, message) => {
  const logElement = document.getElementById('docker-logs');
  logElement.innerHTML += message + '\n';
  logElement.scrollTop = logElement.scrollHeight;
});

ipcRenderer.on('docker-status', (event, status) => {
  dockerStatus = status;
  const indicator = document.getElementById('docker-status-indicator');

  switch (status) {
    case 'running':
      indicator.textContent = 'Running';
      indicator.className = 'badge bg-success me-2';
      break;
    case 'stopped':
      indicator.textContent = 'Stopped';
      indicator.className = 'badge bg-danger me-2';
      break;
    case 'error':
      indicator.textContent = 'Error';
      indicator.className = 'badge bg-danger me-2';
      break;
    default:
      indicator.textContent = 'Unknown';
      indicator.className = 'badge bg-secondary me-2';
  }

  updateNetworkStatus();
});
