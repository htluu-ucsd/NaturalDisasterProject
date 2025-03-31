import os
import numpy as np
import pandas as pd
import netCDF4
from datetime import datetime
import matplotlib.pyplot as plt
from pathlib import Path

"""
Example Usage:
    # Create processor instance
    processor = NetCDFProcessor("/path/to/netcdf/files")

    # Load a file
    processor.load_file("my_data.nc")

    # Describe the dataset structure
    info = processor.describe_dataset()
    print(info)
"""
class NetCDFProcessor:
    """
    A general-purpose class for processing NetCDF (.nc) files.
    """
    
    def __init__(self, data_directory=None):
        """
        Initialize the NetCDF processor.
        
        Parameters:
        - data_directory: Path to directory containing NetCDF files
        """
        self.data_directory = data_directory
        self.current_dataset = None
        self.file_date = None
    
    def load_file(self, file_path):
        """
        Load a NetCDF file.
        
        Parameters:
        - file_path: Path to the NetCDF file
        
        Returns:
        - Dataset object
        """
        print(f"Loading NetCDF file: {os.path.basename(file_path)}")
        
        if self.current_dataset is not None:
            self.current_dataset.close()
            
        self.current_dataset = netCDF4.Dataset(file_path, mode="r")
        filename = os.path.basename(file_path)
        if '_' in filename:
            parts = filename.split('_')
            for part in parts:
                if len(part) >= 8 and part[:8].isdigit():
                    try:
                        self.file_date = datetime.strptime(part[:8], "%Y%m%d").date()
                        break
                    except ValueError:
                        pass
        
        return self.current_dataset
    
    def describe_dataset(self):
        """
        Describe the content of the currently loaded NetCDF file.
        
        Returns:
        - Dictionary with dataset information
        """
        if self.current_dataset is None:
            raise ValueError("No dataset loaded. Call load_file() first.")
        
        info = {
            'dimensions': {},
            'variables': {},
            'global_attributes': {}
        }
        
        # Get dimensions
        for dim_name, dim in self.current_dataset.dimensions.items():
            info['dimensions'][dim_name] = {
                'size': len(dim),
                'unlimited': dim.isunlimited()
            }
        
        # Get variables
        for var_name, var in self.current_dataset.variables.items():
            info['variables'][var_name] = {
                'dimensions': var.dimensions,
                'shape': var.shape,
                'dtype': var.dtype,
                'attributes': {attr: var.getncattr(attr) for attr in var.ncattrs()}
            }
        
        # Get global attributes
        for attr in self.current_dataset.ncattrs():
            info['global_attributes'][attr] = self.current_dataset.getncattr(attr)
        
        return info
    
    def get_variable_data(self, var_name, indices=None):
        """
        Get data for a specific variable.
        
        Parameters:
        - var_name: Name of the variable
        - indices: Optional dictionary mapping dimension names to indices or slices
        
        Returns:
        - NumPy array with variable data
        """
        if self.current_dataset is None:
            raise ValueError("No dataset loaded. Call load_file() first.")
        
        if var_name not in self.current_dataset.variables:
            raise ValueError(f"Variable '{var_name}' not found in dataset.")
        
        var = self.current_dataset.variables[var_name]
        
        if indices is None:
            return var[:]
        
        # Create a list of slices for each dimension
        slices = []
        for dim in var.dimensions:
            if dim in indices:
                slices.append(indices[dim])
            else:
                slices.append(slice(None))
        
        return var[tuple(slices)]
    
    def get_value_at_coordinates(self, var_name, coords, coord_vars=None, time_idx=0):
        """
        Get value at specific coordinates.
        
        Parameters:
        - var_name: Name of the variable to extract
        - coords: Dictionary mapping coordinate names to values
        - coord_vars: Dictionary mapping coordinate names to NetCDF variable names
        - time_idx: Time index (default 0 for first time step)
        
        Returns:
        - Value at the specified coordinates
        """
        if self.current_dataset is None:
            raise ValueError("No dataset loaded. Call load_file() first.")
        
        if var_name not in self.current_dataset.variables:
            raise ValueError(f"Variable '{var_name}' not found in dataset.")
        
        var = self.current_dataset.variables[var_name]
        if coord_vars is None:
            coord_vars = {}
            for dim in var.dimensions:
                if dim in self.current_dataset.variables:
                    coord_vars[dim] = dim
        
        indices = {}
        distances = {}
        
        for coord_name, coord_value in coords.items():
            if coord_name not in coord_vars:
                continue
                
            var_name = coord_vars[coord_name]
            coord_data = self.current_dataset.variables[var_name][:]
            
            # Find nearest index
            idx = np.abs(coord_data - coord_value).argmin()
            actual_value = coord_data[idx]
            distance = abs(actual_value - coord_value)
            
            indices[coord_name] = idx
            distances[coord_name] = distance
        var_slices = []
        for dim in var.dimensions:
            if dim == 'time' and 'time' not in coords:
                var_slices.append(time_idx)
            elif dim in indices:
                var_slices.append(indices[dim])
            else:
                var_slices.append(slice(None))
        value = var[tuple(var_slices)]
        
        # Handle masked values
        if hasattr(value, 'mask') and np.ma.is_masked(value):
            return np.nan, distances
        else:
            return float(value.item()) if hasattr(value, 'item') else value, distances
