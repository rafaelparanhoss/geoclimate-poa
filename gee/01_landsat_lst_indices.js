// geoclimate-poa
// Diagnostico Landsat 8/9 Collection 2 Level 2 para Porto Alegre.
//
// Este script gera uma composicao diagnostica para o verao 2023/2024.
// Ele nao exporta arquivos. Use o console e as camadas do mapa para
// validar cobertura, mascaras e faixas de valores antes das estatisticas
// zonais.

// ---------------------------------------------------------------------
// 1. Parametros
// ---------------------------------------------------------------------

var PROJECT_NAME = 'geoclimate-poa';
var MUNICIPAL_ASSET = 'projects/rafaelparanhoss/assets/limite_municipal_poa_vigente';
var LANDSAT_8_COLLECTION = 'LANDSAT/LC08/C02/T1_L2';
var LANDSAT_9_COLLECTION = 'LANDSAT/LC09/C02/T1_L2';

var START_DATE = '2023-12-01';
var END_DATE = '2024-03-31';
var END_DATE_EXCLUSIVE = ee.Date(END_DATE).advance(1, 'day');

var SCALE = 30;
var TILE_SCALE = 4;
var MIN_VALID_OBS_FOR_LST = 5;
var N_OBS_VIS_MAX = 13;

// ---------------------------------------------------------------------
// 2. Area de estudo validada
// ---------------------------------------------------------------------

var limiteMunicipal = ee.FeatureCollection(MUNICIPAL_ASSET);
var aoi = limiteMunicipal.geometry();

Map.centerObject(aoi, 11);
Map.addLayer(
  limiteMunicipal.style({
    color: '202020',
    fillColor: '00000000',
    width: 2
  }),
  {},
  'Limite municipal POA - asset validado',
  true
);

// ---------------------------------------------------------------------
// 3. Funcoes Landsat Collection 2 Level 2
// ---------------------------------------------------------------------

function maskLandsatC2L2(image) {
  // QA_PIXEL bits usados:
  // bit 0: fill
  // bit 1: dilated cloud
  // bit 2: cirrus
  // bit 3: cloud
  // bit 4: cloud shadow
  // bit 5: snow
  var qa = image.select('QA_PIXEL');
  var clearMask = qa.bitwiseAnd(1 << 0).eq(0)
    .and(qa.bitwiseAnd(1 << 1).eq(0))
    .and(qa.bitwiseAnd(1 << 2).eq(0))
    .and(qa.bitwiseAnd(1 << 3).eq(0))
    .and(qa.bitwiseAnd(1 << 4).eq(0))
    .and(qa.bitwiseAnd(1 << 5).eq(0));

  // QA_RADSAT igual a zero remove pixels com saturacao radiometrica.
  var saturationMask = image.select('QA_RADSAT').eq(0);

  return ee.Image(image)
    .updateMask(clearMask)
    .updateMask(saturationMask);
}

function applyScaleFactors(image) {
  image = ee.Image(image);

  // Surface reflectance:
  // reflectancia = DN * 0.0000275 - 0.2
  var optical = image
    .select(
      ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'],
      ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
    )
    .multiply(0.0000275)
    .add(-0.2);

  // Surface temperature:
  // Kelvin = DN * 0.00341802 + 149.0
  // Celsius = Kelvin - 273.15
  var lstC = image
    .select('ST_B10')
    .multiply(0.00341802)
    .add(149.0)
    .subtract(273.15)
    .rename('LST_C');

  return ee.Image(
    ee.Image.cat([optical, lstC])
      .copyProperties(image, image.propertyNames())
  );
}

function normalizedDifferenceByExpression(image, bandA, bandB, outputName) {
  image = ee.Image(image);
  return image
    .expression(
      '(a - b) / (a + b)',
      {
        a: image.select(bandA),
        b: image.select(bandB)
      }
    )
    .rename(outputName);
}

function addSpectralIndices(image) {
  image = ee.Image(image);

  var ndvi = normalizedDifferenceByExpression(image, 'nir', 'red', 'NDVI');
  var ndbi = normalizedDifferenceByExpression(image, 'swir1', 'nir', 'NDBI');
  var mndwi = normalizedDifferenceByExpression(image, 'green', 'swir1', 'MNDWI');

  return ee.Image(
    image
      .addBands([ndvi, ndbi, mndwi])
      .select(['LST_C', 'NDVI', 'NDBI', 'MNDWI', 'blue', 'green', 'red'])
      .copyProperties(image, image.propertyNames())
  );
}

function prepareLandsatImage(image) {
  return addSpectralIndices(applyScaleFactors(maskLandsatC2L2(image)));
}

function buildLandsatCollection(collectionId) {
  return ee.ImageCollection(collectionId)
    .filterBounds(aoi)
    .filterDate(START_DATE, END_DATE_EXCLUSIVE)
    .filter(ee.Filter.eq('PROCESSING_LEVEL', 'L2SP'));
}

// ---------------------------------------------------------------------
// 4. Colecoes Landsat 8/9 harmonizadas
// ---------------------------------------------------------------------

var landsat8Raw = buildLandsatCollection(LANDSAT_8_COLLECTION);
var landsat9Raw = buildLandsatCollection(LANDSAT_9_COLLECTION);
var landsatRaw = landsat8Raw.merge(landsat9Raw).sort('system:time_start');

var landsat = landsatRaw
  .map(prepareLandsatImage)
  .sort('system:time_start');

// ---------------------------------------------------------------------
// 5. Composicao diagnostica
// ---------------------------------------------------------------------

var lstStats = landsat
  .select('LST_C')
  .reduce(ee.Reducer.percentile([50, 75, 90]))
  .rename(['LST_C_median', 'LST_C_p75', 'LST_C_p90']);

var indexMedians = landsat
  .select(['NDVI', 'NDBI', 'MNDWI'])
  .median()
  .rename(['NDVI_median', 'NDBI_median', 'MNDWI_median']);

var nObsValidas = landsat
  .select('LST_C')
  .count()
  .unmask(0)
  .rename('n_obs_validas');

var lstValidMask = nObsValidas
  .gte(MIN_VALID_OBS_FOR_LST)
  .rename('lst_valid_mask');

var composite = ee.Image
  .cat([lstStats, indexMedians, nObsValidas, lstValidMask])
  .clip(aoi);

// ---------------------------------------------------------------------
// 6. Visualizacao
// ---------------------------------------------------------------------

var lstVis = {
  min: 20,
  max: 45,
  palette: ['2166ac', '67a9cf', 'f7f7f7', 'fdae61', 'b2182b']
};

var ndviVis = {
  min: -0.2,
  max: 0.8,
  palette: ['8c510a', 'f6e8c3', '1a9850']
};

var ndbiVis = {
  min: -0.5,
  max: 0.5,
  palette: ['2166ac', 'f7f7f7', 'b2182b']
};

var mndwiVis = {
  min: -0.5,
  max: 0.5,
  palette: ['8c510a', 'f6e8c3', '01665e']
};

var nObsVis = {
  min: 0,
  max: N_OBS_VIS_MAX,
  palette: ['f7f7f7', 'd9f0a3', '78c679', '238443']
};

var invalidLstVis = {
  min: 0,
  max: 1,
  palette: ['ff00ff']
};

Map.addLayer(
  composite.select('LST_C_median'),
  lstVis,
  'LST_C mediana - verao 2023/2024',
  true
);

Map.addLayer(
  composite.select('LST_C_p75'),
  lstVis,
  'LST_C p75 - verao 2023/2024',
  false
);

Map.addLayer(
  composite.select('LST_C_p90'),
  lstVis,
  'LST_C p90 - verao 2023/2024',
  false
);

Map.addLayer(
  composite.select('NDVI_median'),
  ndviVis,
  'NDVI mediano',
  true
);

Map.addLayer(
  composite.select('NDBI_median'),
  ndbiVis,
  'NDBI mediano',
  false
);

Map.addLayer(
  composite.select('MNDWI_median'),
  mndwiVis,
  'MNDWI mediano',
  false
);

Map.addLayer(
  composite.select('n_obs_validas'),
  nObsVis,
  'Numero de observacoes validas',
  true
);

Map.addLayer(
  composite.select('lst_valid_mask').eq(0).selfMask(),
  invalidLstVis,
  'Pixels sem LST valida (n_obs < 5)',
  false
);

// ---------------------------------------------------------------------
// 7. Diagnosticos no console
// ---------------------------------------------------------------------

var imageDates = ee.List(landsatRaw.aggregate_array('system:time_start'))
  .map(function(timeStart) {
    return ee.Date(timeStart).format('YYYY-MM-dd');
  })
  .distinct()
  .sort();

var imageIds = ee.List(landsatRaw.aggregate_array('LANDSAT_PRODUCT_ID'))
  .sort();

var nObsStats = composite
  .select('n_obs_validas')
  .reduceRegion({
    reducer: ee.Reducer.minMax()
      .combine({
        reducer2: ee.Reducer.mean(),
        sharedInputs: true
      })
      .combine({
        reducer2: ee.Reducer.percentile([25, 50, 75, 90]),
        sharedInputs: true
      }),
    geometry: aoi,
    scale: SCALE,
    maxPixels: 1e9,
    tileScale: TILE_SCALE
  });

var diagnosticStats = composite
  .select([
    'LST_C_median',
    'LST_C_p75',
    'LST_C_p90',
    'NDVI_median',
    'NDBI_median',
    'MNDWI_median'
  ])
  .reduceRegion({
    reducer: ee.Reducer.minMax()
      .combine({
        reducer2: ee.Reducer.mean(),
        sharedInputs: true
      })
      .combine({
        reducer2: ee.Reducer.median(),
        sharedInputs: true
      }),
    geometry: aoi,
    scale: SCALE,
    maxPixels: 1e9,
    tileScale: TILE_SCALE
  });

var totalAreaM2 = ee.Image.pixelArea()
  .rename('area_m2')
  .reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: aoi,
    scale: SCALE,
    maxPixels: 1e9,
    tileScale: TILE_SCALE
  })
  .get('area_m2');

function pctAreaWithMinObservations(minObs) {
  var validAreaM2 = ee.Image.pixelArea()
    .rename('area_m2')
    .updateMask(nObsValidas.gte(minObs))
    .reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: aoi,
      scale: SCALE,
      maxPixels: 1e9,
      tileScale: TILE_SCALE
    })
    .get('area_m2');

  validAreaM2 = ee.Number(
    ee.Algorithms.If(
      ee.Algorithms.IsEqual(validAreaM2, null),
      0,
      validAreaM2
    )
  );

  return validAreaM2
    .divide(ee.Number(totalAreaM2))
    .multiply(100);
}

var observationCoveragePct = ee.Dictionary({
  pct_area_n_obs_ge_1: pctAreaWithMinObservations(1),
  pct_area_n_obs_ge_3: pctAreaWithMinObservations(3),
  pct_area_n_obs_ge_5: pctAreaWithMinObservations(5),
  pct_area_n_obs_ge_7: pctAreaWithMinObservations(7)
});

print('Projeto', PROJECT_NAME);
print('Periodo analisado', START_DATE + ' a ' + END_DATE);
print('Asset municipal', MUNICIPAL_ASSET);
print('Features no limite municipal', limiteMunicipal.size());
print('Area municipal aproximada km2', ee.Number(aoi.area(1)).divide(1e6));
print('Numero de imagens Landsat 8', landsat8Raw.size());
print('Numero de imagens Landsat 9', landsat9Raw.size());
print('Numero total de imagens Landsat 8/9', landsatRaw.size());
print('Datas das imagens usadas', imageDates);
print('LANDSAT_PRODUCT_ID das imagens usadas', imageIds);
print('Estatisticas de n_obs_validas', nObsStats);
print('Estatisticas das bandas diagnosticas', diagnosticStats);
print('Cobertura percentual por limiares de observacoes validas', observationCoveragePct);
print('Bandas finais da composicao', composite.bandNames());

// Sem Export neste script.
