// Google Earth Engine placeholder for zonal statistics by bairro.
//
// Planned outputs:
// - Mean land surface temperature by bairro.
// - Mean vegetation and urbanization indices by bairro.
// - Exported tables for downstream Python processing.
//
// TODO: Load bairro boundaries, attach raster indicators, reduce regions,
// and export tables to Google Drive or Cloud Storage.

var projectName = 'geoclimate-poa';
var spatialUnit = 'bairros';

print('Project:', projectName);
print('Spatial unit:', spatialUnit);

