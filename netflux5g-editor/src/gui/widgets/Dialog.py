"""
Property dialog windows for all network components.
Each dialog loads its UI from the corresponding .ui file and handles component configuration.
"""

import os
import yaml
from PyQt5.QtWidgets import (QMainWindow, QDialog, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QMessageBox, QFileDialog,
                             QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLineEdit,
                             QLabel, QPushButton, QTextEdit, QFormLayout, QComboBox,
                             QSpinBox, QDoubleSpinBox, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.uic import loadUi
from ..debug_manager import debug_print, error_print, warning_print

class BasePropertiesWindow(QMainWindow):
    """Base class for all property windows with common functionality."""
    
    properties_updated = pyqtSignal(dict)
    
    def __init__(self, ui_file, label_text="Component", parent=None, component=None):
        super().__init__(parent)
        self.component = component
        self.label_text = label_text
        
        # Load UI file
        ui_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", ui_file)
        if os.path.exists(ui_path):
            try:
                loadUi(ui_path, self)
                debug_print(f"Loaded UI file: {ui_path}")
            except Exception as e:
                error_print(f"Failed to load UI file {ui_path}: {e}")
                self._create_fallback_ui()
        else:
            error_print(f"UI file not found: {ui_path}")
            self._create_fallback_ui()
        
        self.setWindowTitle(f"{label_text} Properties")
        self._setup_connections()
        self._load_component_properties()
    
    def _create_fallback_ui(self):
        """Create a basic fallback UI if the .ui file cannot be loaded."""
        from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QHBoxLayout
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Form layout for properties
        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        layout.addLayout(form_layout)
        
        # Button layout
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setGeometry(100, 100, 400, 200)
    
    def _setup_connections(self):
        """Setup button connections. Override in subclasses for specific UI elements."""
        # Try to connect common button names
        if hasattr(self, 'ok_button') or hasattr(self, f'{self.component.component_type}_OKButton'):
            ok_button = getattr(self, 'ok_button', None) or getattr(self, f'{self.component.component_type}_OKButton', None)
            if ok_button:
                ok_button.clicked.connect(self.accept_changes)
        
        if hasattr(self, 'cancel_button') or hasattr(self, f'{self.component.component_type}_CancelButton'):
            cancel_button = getattr(self, 'cancel_button', None) or getattr(self, f'{self.component.component_type}_CancelButton', None)
            if cancel_button:
                cancel_button.clicked.connect(self.close)
    
    def _load_component_properties(self):
        """Load component properties into the dialog. Override in subclasses."""
        if not self.component:
            return
        
        properties = self.component.getProperties()
        
        # Try to set name field
        name_field = getattr(self, 'name_edit', None) or getattr(self, f'{self.component.component_type}_Name', None)
        if name_field and 'name' in properties:
            name_field.setText(properties['name'])
    
    def accept_changes(self):
        """Save changes and close dialog."""
        try:
            properties = self._collect_properties()
            if self.component:
                self.component.setProperties(properties)
                self.properties_updated.emit(properties)
            self.close()
        except Exception as e:
            error_print(f"Failed to save properties: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save properties: {e}")
    
    def _collect_properties(self):
        """Collect properties from dialog fields. Override in subclasses."""
        properties = {}
        
        # Try to get name field
        name_field = getattr(self, 'name_edit', None) or getattr(self, f'{self.component.component_type}_Name', None)
        if name_field:
            properties['name'] = name_field.text()
        
        return properties

class HostPropertiesWindow(BasePropertiesWindow):
    """Properties dialog for Host components."""
    
    def __init__(self, label_text="Host", parent=None, component=None):
        super().__init__("Host_properties.ui", label_text, parent, component)
    
    def _setup_connections(self):
        super()._setup_connections()
        # Add host-specific connections
        
    def _load_component_properties(self):
        super()._load_component_properties()
        if not self.component:
            return
        
        properties = self.component.getProperties()
        
        # Load host-specific properties
        field_mappings = {
            'Host_Hostname': 'hostname',
            'Host_IPAddress': 'ip_address',
            'Host_DefaultRoute': 'default_route',
            'Host_AmountCPU': 'cpu',
            'Host_Memory': 'memory'
        }
        
        for field_name, prop_key in field_mappings.items():
            field = getattr(self, field_name, None)
            if field and prop_key in properties:
                if isinstance(field, (QSpinBox, QDoubleSpinBox)):
                    field.setValue(float(properties[prop_key]))
                else:
                    field.setText(str(properties[prop_key]))
    
    def _collect_properties(self):
        properties = super()._collect_properties()
        
        # Collect host-specific properties
        field_mappings = {
            'Host_Hostname': 'hostname',
            'Host_IPAddress': 'ip_address', 
            'Host_DefaultRoute': 'default_route',
            'Host_AmountCPU': 'cpu',
            'Host_Memory': 'memory'
        }
        
        for field_name, prop_key in field_mappings.items():
            field = getattr(self, field_name, None)
            if field:
                if isinstance(field, (QSpinBox, QDoubleSpinBox)):
                    properties[prop_key] = field.value()
                else:
                    properties[prop_key] = field.text()
        
        return properties

class STAPropertiesWindow(BasePropertiesWindow):
    """Properties dialog for STA (Station) components."""
    
    def __init__(self, label_text="STA", parent=None, component=None):
        super().__init__("STA_properties.ui", label_text, parent, component)
    
    def _load_component_properties(self):
        super()._load_component_properties()
        if not self.component:
            return
        
        properties = self.component.getProperties()
        
        # Load STA-specific properties
        field_mappings = {
            'STA_Hostname': 'hostname',
            'STA_IPAddress': 'ip_address',
            'STA_MACAddress': 'mac_address',
            'STA_SignalRange': 'signal_range'
        }
        
        for field_name, prop_key in field_mappings.items():
            field = getattr(self, field_name, None)
            if field and prop_key in properties:
                field.setText(str(properties[prop_key]))
    
    def _collect_properties(self):
        properties = super()._collect_properties()
        
        # Collect STA-specific properties
        field_mappings = {
            'STA_Hostname': 'hostname',
            'STA_IPAddress': 'ip_address',
            'STA_MACAddress': 'mac_address', 
            'STA_SignalRange': 'signal_range'
        }
        
        for field_name, prop_key in field_mappings.items():
            field = getattr(self, field_name, None)
            if field:
                properties[prop_key] = field.text()
        
        return properties

class UEPropertiesWindow(BasePropertiesWindow):
    """Properties dialog for UE (User Equipment) components."""
    
    def __init__(self, label_text="UE", parent=None, component=None):
        super().__init__("UE_properties.ui", label_text, parent, component)
    
    def _load_component_properties(self):
        super()._load_component_properties()
        if not self.component:
            return
        
        properties = self.component.getProperties()
        
        # Load UE-specific properties with defaults
        field_mappings = {
            'UE_IMSI': ('imsi', '001010000000001'),
            'UE_MCC': ('mcc', '999'),
            'UE_MNC': ('mnc', '70'),
            'UE_KEY': ('key', '465B5CE8B199B49FAA5F0A2EE238A6BC'),
            'UE_OPType': ('op_type', 'OPC'),
            'UE_OP': ('op', 'E8ED289DEBA952E4283B54E88E6183CA'),
            'UE_AMFHostname': ('amf_hostname', 'mn.amf')
        }
        
        for field_name, (prop_key, default) in field_mappings.items():
            field = getattr(self, field_name, None)
            if field:
                value = properties.get(prop_key, default)
                field.setText(str(value))
    
    def _collect_properties(self):
        properties = super()._collect_properties()
        
        # Collect UE-specific properties
        field_mappings = {
            'UE_IMSI': 'imsi',
            'UE_MCC': 'mcc',
            'UE_MNC': 'mnc',
            'UE_KEY': 'key',
            'UE_OPType': 'op_type',
            'UE_OP': 'op',
            'UE_AMFHostname': 'amf_hostname'
        }
        
        for field_name, prop_key in field_mappings.items():
            field = getattr(self, field_name, None)
            if field:
                properties[prop_key] = field.text()
        
        return properties

class GNBPropertiesWindow(BasePropertiesWindow):
    """Properties dialog for gNB (Next Generation NodeB) components."""
    
    def __init__(self, label_text="gNB", parent=None, component=None):
        super().__init__("GNB_properties.ui", label_text, parent, component)
    
    def _load_component_properties(self):
        super()._load_component_properties()
        if not self.component:
            return
        
        properties = self.component.getProperties()
        
        # Load gNB-specific properties with defaults
        field_mappings = {
            'GNB_Hostname': ('hostname', 'mn.gnb'),
            'GNB_AMF_IP': ('amf_ip', '10.0.0.3'),
            'GNB_MCC': ('mcc', '999'),
            'GNB_MNC': ('mnc', '70'),
            'GNB_SST': ('sst', '1'),
            'GNB_SD': ('sd', '0xffffff'),
            'GNB_TAC': ('tac', '1'),
            'GNB_Power': ('power', '20')
        }
        
        for field_name, (prop_key, default) in field_mappings.items():
            field = getattr(self, field_name, None)
            if field:
                value = properties.get(prop_key, default)
                field.setText(str(value))
    
    def _collect_properties(self):
        properties = super()._collect_properties()
        
        # Collect gNB-specific properties
        field_mappings = {
            'GNB_Hostname': 'hostname',
            'GNB_AMF_IP': 'amf_ip',
            'GNB_MCC': 'mcc',
            'GNB_MNC': 'mnc',
            'GNB_SST': 'sst',
            'GNB_SD': 'sd',
            'GNB_TAC': 'tac',
            'GNB_Power': 'power'
        }
        
        for field_name, prop_key in field_mappings.items():
            field = getattr(self, field_name, None)
            if field:
                properties[prop_key] = field.text()
        
        return properties

class APPropertiesWindow(BasePropertiesWindow):
    """Properties dialog for Access Point components."""
    
    def __init__(self, label_text="AP", parent=None, component=None):
        super().__init__("AP_properties.ui", label_text, parent, component)

class DockerHostPropertiesWindow(BasePropertiesWindow):
    """Properties dialog for Docker Host components."""
    
    def __init__(self, label_text="Docker Host", parent=None, component=None):
        super().__init__("DockerHost_properties.ui", label_text, parent, component)

class ControllerPropertiesWindow(BasePropertiesWindow):
    """Properties dialog for Controller components."""
    
    def __init__(self, label_text="Controller", parent=None, component=None):
        super().__init__("Controller_properties.ui", label_text, parent, component)

class Component5GPropertiesWindow(BasePropertiesWindow):
    """Properties dialog for 5G Core components with advanced configuration management."""
    
    def __init__(self, label_text="5G Core", parent=None, component=None):
        super().__init__("Component5G_properties.ui", label_text, parent, component)
        self._setup_5g_specific_ui()
    
    def _setup_5g_specific_ui(self):
        """Setup 5G-specific UI elements and tables."""
        # Setup component configuration tables for different 5G components
        self.component_configs = {
            'UPF': [], 'AMF': [], 'SMF': [], 'NRF': [], 'SCP': [],
            'AUSF': [], 'BSF': [], 'NSSF': [], 'PCF': [], 'PCRF': [],
            'UDM': [], 'UDR': []
        }
        
        # Setup tables for each component type if they exist
        component_types = ['UPF', 'AMF', 'SMF', 'NRF', 'SCP', 'AUSF', 'BSF', 'NSSF', 'PCF', 'PCRF', 'UDM', 'UDR']
        
        for comp_type in component_types:
            table_name = f"{comp_type}_Table"
            if hasattr(self, table_name):
                table = getattr(self, table_name)
                self._setup_component_table(table, comp_type)
    
    def _setup_component_table(self, table, component_type):
        """Setup a component configuration table."""
        # Set table properties
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Name", "Config File", "Settings", "Import", "Remove"])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # Enable selection
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Add context menu
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(
            lambda pos, ct=component_type, tb=table: self._show_table_context_menu(pos, ct, tb)
        )
    
    def _show_table_context_menu(self, pos, component_type, table):
        """Show context menu for component table."""
        from PyQt5.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        # Add component action
        add_action = menu.addAction(f"Add {component_type}")
        add_action.triggered.connect(lambda: self._add_component_config(component_type, table))
        
        # Import config action
        import_action = menu.addAction("Import Configuration")
        import_action.triggered.connect(lambda: self._import_component_config(component_type, table))
        
        # Remove selected action
        if table.currentRow() >= 0:
            remove_action = menu.addAction("Remove Selected")
            remove_action.triggered.connect(lambda: self._remove_component_config(component_type, table))
        
        menu.exec_(table.mapToGlobal(pos))
    
    def _add_component_config(self, component_type, table):
        """Add a new component configuration."""
        # Create default configuration
        config = {
            'name': f"{component_type.lower()}{table.rowCount() + 1}",
            'config_file': f"{component_type.lower()}.yaml",
            'settings': '',
            'imported': False,
            'config_content': {},
            'config_file_path': ''
        }
        
        # Add to table
        self._add_config_to_table(table, config, component_type)
        
        # Store in component configs
        if component_type not in self.component_configs:
            self.component_configs[component_type] = []
        self.component_configs[component_type].append(config)
    
    def _import_component_config(self, component_type, table):
        """Import a configuration file for a component."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Import {component_type} Configuration",
            "",
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config_content = yaml.safe_load(f)
                
                # Create configuration entry
                config = {
                    'name': f"{component_type.lower()}_imported",
                    'config_file': os.path.basename(file_path),
                    'settings': '',
                    'imported': True,
                    'config_content': config_content,
                    'config_file_path': file_path
                }
                
                # Add to table
                self._add_config_to_table(table, config, component_type)
                
                # Store in component configs
                if component_type not in self.component_configs:
                    self.component_configs[component_type] = []
                self.component_configs[component_type].append(config)
                
                QMessageBox.information(self, "Import Successful", f"Configuration imported from {file_path}")
                
            except Exception as e:
                QMessageBox.warning(self, "Import Error", f"Failed to import configuration: {e}")
    
    def _add_config_to_table(self, table, config, component_type):
        """Add a configuration to the table."""
        row = table.rowCount()
        table.insertRow(row)
        
        # Name column
        name_item = QTableWidgetItem(config['name'])
        table.setItem(row, 0, name_item)
        
        # Config file column
        config_file_item = QTableWidgetItem(config['config_file'])
        table.setItem(row, 1, config_file_item)
        
        # Settings column
        settings_item = QTableWidgetItem(config.get('settings', ''))
        table.setItem(row, 2, settings_item)
        
        # Import button column
        import_button = QPushButton("Import")
        import_button.clicked.connect(lambda: self._import_component_config(component_type, table))
        table.setCellWidget(row, 3, import_button)
        
        # Remove button column
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self._remove_table_row(table, row, component_type))
        table.setCellWidget(row, 4, remove_button)
    
    def _remove_component_config(self, component_type, table):
        """Remove selected component configuration."""
        current_row = table.currentRow()
        if current_row >= 0:
            self._remove_table_row(table, current_row, component_type)
    
    def _remove_table_row(self, table, row, component_type):
        """Remove a row from the table and update configurations."""
        if 0 <= row < table.rowCount():
            table.removeRow(row)
            
            # Update component configs
            if component_type in self.component_configs and row < len(self.component_configs[component_type]):
                del self.component_configs[component_type][row]
    
    def _collect_properties(self):
        """Collect properties including all component configurations."""
        properties = super()._collect_properties()
        
        # Collect configurations from all tables
        for component_type in self.component_configs:
            table_name = f"{component_type}_Table"
            if hasattr(self, table_name):
                table = getattr(self, table_name)
                configs = self._collect_table_configs(table)
                properties[f"{component_type}_configs"] = configs
        
        return properties
    
    def _collect_table_configs(self, table):
        """Collect configurations from a table."""
        configs = []
        
        for row in range(table.rowCount()):
            name_item = table.item(row, 0)
            config_file_item = table.item(row, 1)
            settings_item = table.item(row, 2)
            
            if name_item and config_file_item:
                config = {
                    'name': name_item.text(),
                    'config_file': config_file_item.text(),
                    'settings': settings_item.text() if settings_item else '',
                    'imported': False,
                    'config_content': {},
                    'config_file_path': ''
                }
                configs.append(config)
        
        return configs

# Dialog factory function
def create_properties_dialog(component_type, label_text, parent=None, component=None):
    """Factory function to create the appropriate properties dialog."""
    dialog_map = {
        "Host": HostPropertiesWindow,
        "STA": STAPropertiesWindow,
        "UE": UEPropertiesWindow,
        "GNB": GNBPropertiesWindow,
        "DockerHost": DockerHostPropertiesWindow,
        "AP": APPropertiesWindow,
        "VGcore": Component5GPropertiesWindow,
        "Controller": ControllerPropertiesWindow,
    }
    
    dialog_class = dialog_map.get(component_type, BasePropertiesWindow)
    return dialog_class(label_text, parent, component)
