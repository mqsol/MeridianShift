from qgis.core import (
    QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsFeature, QgsGeometry, QgsVectorFileWriter
)
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog

# MeridianShift Projection with Central Meridian at 135°
CUSTOM_CRS = "+proj=wintri +lon_0=135 +datum=WGS84 +no_defs"

class MeridianShift(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Layer selection
        self.layer_label = QLabel("Select Layer:")
        self.layer_combo = QComboBox()
        self.populate_layers()
        layout.addWidget(self.layer_label)
        layout.addWidget(self.layer_combo)
        
        # Projection selection (Only MeridianShift)
        self.projection_label = QLabel("Projection: MeridianShift (Central Meridian 135°)")
        layout.addWidget(self.projection_label)
        
        # Output file selection
        self.output_button = QPushButton("Select Output File")
        self.output_button.clicked.connect(self.select_output_file)
        layout.addWidget(self.output_button)
        
        # Run transformation button
        self.run_button = QPushButton("Run Transformation")
        self.run_button.clicked.connect(self.run_transformation)
        layout.addWidget(self.run_button)
        
        self.setLayout(layout)
    
    def populate_layers(self):
        self.layer_combo.clear()
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            self.layer_combo.addItem(layer.name(), layer)
    
    def select_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Layer", "", "Shapefile (*.shp);;GeoJSON (*.geojson)")
        self.output_file = file_path
    
    def run_transformation(self):
        layer = self.layer_combo.currentData()
        if layer and self.output_file:
            reproject_and_fix_layer(layer, self.output_file)
        else:
            print("Please select a layer and output file.")

# Function to reproject and fix geometry
def reproject_and_fix_layer(layer, output_file):
    if not layer:
        print("No layer selected")
        return
    
    # Set Source and Target CRS
    source_crs = layer.crs()
    wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")
    custom_crs = QgsCoordinateReferenceSystem()
    custom_crs.createFromProj(CUSTOM_CRS)
    
    # Convert layer to WGS84 first (if necessary)
    if source_crs.authid() != "EPSG:4326":
        transform = QgsCoordinateTransform(source_crs, wgs84_crs, QgsProject.instance())
        layer = reproject_layer(layer, wgs84_crs, transform)
    
    # Convert layer to MeridianShift (Custom CRS)
    transform = QgsCoordinateTransform(wgs84_crs, custom_crs, QgsProject.instance())
    transformed_layer = reproject_layer(layer, custom_crs, transform)
    
    # Fix Geometry
    fixed_layer = fix_geometry(transformed_layer)
    
    # Save Output
    QgsVectorFileWriter.writeAsVectorFormat(fixed_layer, output_file, "UTF-8", fixed_layer.crs(), "ESRI Shapefile")
    print("Layer saved successfully: ", output_file)

def reproject_layer(layer, target_crs, transform):
    new_layer = QgsVectorLayer("Polygon?crs=" + target_crs.authid(), "Reprojected Layer", "memory")
    new_layer_data = new_layer.dataProvider()
    new_layer_data.addAttributes(layer.fields())
    new_layer.updateFields()
    
    for feature in layer.getFeatures():
        new_feature = QgsFeature()
        new_feature.setGeometry(feature.geometry().transform(transform))
        new_feature.setAttributes(feature.attributes())
        new_layer_data.addFeature(new_feature)
    
    return new_layer

def fix_geometry(layer):
    fixed_layer = QgsVectorLayer("Polygon?crs=" + layer.crs().authid(), "Fixed Layer", "memory")
    fixed_layer_data = fixed_layer.dataProvider()
    fixed_layer_data.addAttributes(layer.fields())
    fixed_layer.updateFields()
    
    for feature in layer.getFeatures():
        geometry = feature.geometry()
        if not geometry.isGeosValid():
            geometry = geometry.makeValid()
        new_feature = QgsFeature()
        new_feature.setGeometry(geometry)
        new_feature.setAttributes(feature.attributes())
        fixed_layer_data.addFeature(new_feature)
    
    return fixed_layer

