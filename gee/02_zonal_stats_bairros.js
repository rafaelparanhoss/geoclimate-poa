// geoclimate-poa
// Estatisticas zonais por bairro com Landsat 8/9 e MapBiomas.
//
// Este script recalcula a composicao Landsat para manter a exportacao
// reproduzivel em um unico arquivo do Google Earth Engine Code Editor.

// ---------------------------------------------------------------------
// 1. Parametros
// ---------------------------------------------------------------------

var PROJECT_NAME = 'geoclimate-poa';
var MUNICIPAL_ASSET = 'projects/rafaelparanhoss/assets/limite_municipal_poa_vigente';
var BAIRROS_ASSET = 'projects/rafaelparanhoss/assets/bairros';
var MAPBIOMAS_ASSET = 'projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_coverage_v2';

var LANDSAT_8_COLLECTION = 'LANDSAT/LC08/C02/T1_L2';
var LANDSAT_9_COLLECTION = 'LANDSAT/LC09/C02/T1_L2';

var START_DATE = '2023-12-01';
var END_DATE = '2024-03-31';
var END_DATE_EXCLUSIVE = ee.Date(END_DATE).advance(1, 'day');

var SCALE = 30;
var TILE_SCALE = 4;
var MIN_VALID_OBS_FOR_LST = 5;

var EXPORT_FOLDER = 'geoclimate_poa';
var EXPORT_NAME = 'poa_bairros_zonal_stats_landsat_mapbiomas_2023_2024';

var VEGETATION_CLASSES = [3, 4, 5, 6, 49, 11, 12, 50];
var VEGETATION_REMAP_VALUES = [1, 1, 1, 1, 1, 1, 1, 1];

var STAT_INPUT_BANDS = [
  'LST_C_median',
  'LST_C_p75',
  'LST_C_p90',
  'NDVI_median',
  'NDBI_median',
  'MNDWI_median',
  'n_obs_validas',
  'lst_valid_mask'
];

var STAT_OUTPUT_COLUMNS = [
  'LST_C_median_mean',
  'LST_C_median_median',
  'LST_C_p75_mean',
  'LST_C_p75_median',
  'LST_C_p90_mean',
  'LST_C_p90_median',
  'NDVI_median_mean',
  'NDVI_median_median',
  'NDBI_median_mean',
  'NDBI_median_median',
  'MNDWI_median_mean',
  'MNDWI_median_median',
  'n_obs_validas_mean',
  'n_obs_validas_median',
  'lst_valid_mask_mean',
  'lst_valid_mask_median'
];

var AREA_COLUMNS = [
  'area_pixel_total_ha',
  'area_land_ha',
  'area_agua_ha',
  'area_urbana_ha',
  'area_vegetacao_ha',
  'area_lst_valid_ha'
];

var EXPORT_SELECTORS = [
  'bairro_nome',
  'n_partes_originais',
  'LST_C_median_mean',
  'LST_C_median_median',
  'LST_C_p75_mean',
  'LST_C_p75_median',
  'LST_C_p90_mean',
  'LST_C_p90_median',
  'NDVI_median_mean',
  'NDVI_median_median',
  'NDBI_median_mean',
  'NDBI_median_median',
  'MNDWI_median_mean',
  'MNDWI_median_median',
  'n_obs_validas_mean',
  'n_obs_validas_median',
  'lst_valid_mask_mean',
  'lst_valid_mask_median',
  'area_bairro_geom_ha',
  'area_pixel_total_ha',
  'area_land_ha',
  'area_agua_ha',
  'area_urbana_ha',
  'area_vegetacao_ha',
  'area_lst_valid_ha',
  'pct_land',
  'pct_agua',
  'pct_urbana_land',
  'pct_vegetacao_land',
  'pct_lst_valid_land'
];

var PREVIEW_SELECTORS = [
  'bairro_nome',
  'n_partes_originais',
  'LST_C_median_mean',
  'pct_urbana_land',
  'pct_vegetacao_land',
  'pct_lst_valid_land',
  'area_land_ha'
];

// ---------------------------------------------------------------------
// 2. Area de estudo e bairros
// ---------------------------------------------------------------------

var limiteMunicipal = ee.FeatureCollection(MUNICIPAL_ASSET);
var aoi = limiteMunicipal.geometry();

var bairrosOriginais = ee.FeatureCollection(BAIRROS_ASSET)
  .filter(ee.Filter.notNull(['NOME']));

var bairroNomes = ee.List(bairrosOriginais.aggregate_array('NOME'))
  .distinct()
  .sort();

var bairros = ee.FeatureCollection(
  bairroNomes.map(function(nome) {
    nome = ee.String(nome);
    var partes = bairrosOriginais.filter(ee.Filter.eq('NOME', nome));
    var geometriaDissolvida = partes.geometry().dissolve(1);

    return ee.Feature(geometriaDissolvida, {
      bairro_nome: nome,
      n_partes_originais: partes.size()
    });
  })
);

Map.centerObject(aoi, 11);
Map.addLayer(
  limiteMunicipal.style({
    color: '202020',
    fillColor: '00000000',
    width: 2
  }),
  {},
  'Limite municipal POA',
  true
);
Map.addLayer(
  bairros.style({
    color: '666666',
    fillColor: '00000000',
    width: 1
  }),
  {},
  'Bairros dissolvidos por NOME',
  false
);

// ---------------------------------------------------------------------
// 3. Funcoes Landsat Collection 2 Level 2
// ---------------------------------------------------------------------

function maskLandsatC2L2(image) {
  var qa = image.select('QA_PIXEL');
  var clearMask = qa.bitwiseAnd(1 << 0).eq(0)
    .and(qa.bitwiseAnd(1 << 1).eq(0))
    .and(qa.bitwiseAnd(1 << 2).eq(0))
    .and(qa.bitwiseAnd(1 << 3).eq(0))
    .and(qa.bitwiseAnd(1 << 4).eq(0))
    .and(qa.bitwiseAnd(1 << 5).eq(0));

  var saturationMask = image.select('QA_RADSAT').eq(0);

  return ee.Image(image)
    .updateMask(clearMask)
    .updateMask(saturationMask);
}

function applyScaleFactors(image) {
  image = ee.Image(image);

  var optical = image
    .select(
      ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'],
      ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
    )
    .multiply(0.0000275)
    .add(-0.2);

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
// 4. Composicao Landsat
// ---------------------------------------------------------------------

var landsat8Raw = buildLandsatCollection(LANDSAT_8_COLLECTION);
var landsat9Raw = buildLandsatCollection(LANDSAT_9_COLLECTION);
var landsatRaw = landsat8Raw.merge(landsat9Raw).sort('system:time_start');

var landsat = landsatRaw
  .map(prepareLandsatImage)
  .sort('system:time_start');

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
// 5. MapBiomas 2023 e mascaras tematicas
// ---------------------------------------------------------------------

var mapbiomas2023 = ee.Image(MAPBIOMAS_ASSET)
  .select('classification_2023')
  .clip(aoi);

var waterMask = mapbiomas2023.eq(33).rename('water_mask');
var landMask = mapbiomas2023.neq(33).rename('land_mask');
var urbanMask = mapbiomas2023.eq(24).rename('urban_mask');
var vegetationMask = mapbiomas2023
  .remap(VEGETATION_CLASSES, VEGETATION_REMAP_VALUES, 0)
  .eq(1)
  .rename('vegetation_mask');

Map.addLayer(
  composite.select('LST_C_median'),
  {
    min: 20,
    max: 45,
    palette: ['2166ac', '67a9cf', 'f7f7f7', 'fdae61', 'b2182b']
  },
  'LST_C mediana',
  false
);
Map.addLayer(
  urbanMask.selfMask(),
  {palette: ['b2182b']},
  'MapBiomas urbano classe 24',
  false
);
Map.addLayer(
  vegetationMask.selfMask(),
  {palette: ['1a9850']},
  'MapBiomas vegetacao agrupada',
  false
);
Map.addLayer(
  waterMask.selfMask(),
  {palette: ['2166ac']},
  'MapBiomas agua classe 33',
  false
);

// ---------------------------------------------------------------------
// 6. Estatisticas por bairro
// ---------------------------------------------------------------------

var statsImage = composite
  .select(STAT_INPUT_BANDS)
  .updateMask(landMask);

var statsReducer = ee.Reducer.mean()
  .combine({
    reducer2: ee.Reducer.median(),
    sharedInputs: true
  });

var pixelAreaHa = ee.Image.pixelArea().divide(10000);

// As imagens de area usam unmask(0) para evitar nulos quando um bairro
// nao contem agua, vegetacao, urbano ou pixels LST validos.
var areaImage = ee.Image.cat([
  pixelAreaHa.rename('area_pixel_total_ha').unmask(0),
  pixelAreaHa.updateMask(landMask).rename('area_land_ha').unmask(0),
  pixelAreaHa.updateMask(waterMask).rename('area_agua_ha').unmask(0),
  pixelAreaHa.updateMask(urbanMask).rename('area_urbana_ha').unmask(0),
  pixelAreaHa.updateMask(vegetationMask).rename('area_vegetacao_ha').unmask(0),
  pixelAreaHa
    .updateMask(landMask)
    .updateMask(composite.select('lst_valid_mask').eq(1))
    .rename('area_lst_valid_ha')
    .unmask(0)
]);

function fillDictionary(dictionary, keys, fallback) {
  dictionary = ee.Dictionary(dictionary);
  var keyList = ee.List(keys);

  return ee.Dictionary.fromLists(
    keyList,
    keyList.map(function(key) {
      key = ee.String(key);
      var value = dictionary.get(key);

      return ee.Algorithms.If(
        ee.Algorithms.IsEqual(value, null),
        fallback,
        value
      );
    })
  );
}

function pct(numerator, denominator) {
  numerator = ee.Number(numerator);
  denominator = ee.Number(denominator);

  return ee.Number(
    ee.Algorithms.If(
      denominator.gt(0),
      numerator.divide(denominator).multiply(100),
      0
    )
  );
}

function buildBairroStats(feature) {
  feature = ee.Feature(feature);
  var geom = feature.geometry();

  var rawStats = statsImage.reduceRegion({
    reducer: statsReducer,
    geometry: geom,
    scale: SCALE,
    maxPixels: 1e9,
    tileScale: TILE_SCALE
  });

  var rawAreas = areaImage.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geom,
    scale: SCALE,
    maxPixels: 1e9,
    tileScale: TILE_SCALE
  });

  // Fallback -9999 so o torna explicito caso algum bairro fique sem
  // pixels validos para uma estatistica diagnostica.
  var stats = fillDictionary(rawStats, STAT_OUTPUT_COLUMNS, -9999);
  var areas = fillDictionary(rawAreas, AREA_COLUMNS, 0);

  var areaPixelTotalHa = ee.Number(areas.get('area_pixel_total_ha'));
  var areaLandHa = ee.Number(areas.get('area_land_ha'));
  var areaAguaHa = ee.Number(areas.get('area_agua_ha'));
  var areaUrbanaHa = ee.Number(areas.get('area_urbana_ha'));
  var areaVegetacaoHa = ee.Number(areas.get('area_vegetacao_ha'));
  var areaLstValidHa = ee.Number(areas.get('area_lst_valid_ha'));

  return ee.Feature(geom, {
    bairro_nome: feature.get('bairro_nome'),
    n_partes_originais: feature.get('n_partes_originais')
  })
    .set(stats)
    .set(areas)
    .set({
      area_bairro_geom_ha: geom.area(1).divide(10000),
      pct_land: pct(areaLandHa, areaPixelTotalHa),
      pct_agua: pct(areaAguaHa, areaPixelTotalHa),
      pct_urbana_land: pct(areaUrbanaHa, areaLandHa),
      pct_vegetacao_land: pct(areaVegetacaoHa, areaLandHa),
      pct_lst_valid_land: pct(areaLstValidHa, areaLandHa)
    });
}

var tabelaBairros = bairros.map(buildBairroStats);
var tabelaExport = tabelaBairros.select(EXPORT_SELECTORS);

// ---------------------------------------------------------------------
// 7. Diagnosticos no console
// ---------------------------------------------------------------------

var duplicateCount = ee.Number(tabelaExport.size())
  .subtract(ee.List(tabelaExport.aggregate_array('bairro_nome')).distinct().size());

var imageDates = ee.List(landsatRaw.aggregate_array('system:time_start'))
  .map(function(timeStart) {
    return ee.Date(timeStart).format('YYYY-MM-dd');
  })
  .distinct()
  .sort();

print('Projeto', PROJECT_NAME);
print('Periodo Landsat', START_DATE + ' a ' + END_DATE);
print('Features no limite municipal', limiteMunicipal.size());
print('Area municipal aproximada km2', ee.Number(aoi.area(1)).divide(1e6));
print('Numero de imagens Landsat 8', landsat8Raw.size());
print('Numero de imagens Landsat 9', landsat9Raw.size());
print('Numero total de imagens Landsat 8/9', landsatRaw.size());
print('Datas das imagens usadas', imageDates);
print('Numero de feicoes originais de bairros', bairrosOriginais.size());
print('Numero de bairros unicos apos dissolve por NOME', bairros.size());
print('Numero de linhas na tabela final', tabelaExport.size());
print('Nomes duplicados na tabela final', duplicateCount);
print('Primeiras linhas da tabela', tabelaExport.select(PREVIEW_SELECTORS).limit(10));
print(
  'Top 10 por LST_C_median_mean',
  tabelaExport
    .sort('LST_C_median_mean', false)
    .select(PREVIEW_SELECTORS)
    .limit(10)
);
print(
  'Top 10 por pct_urbana_land',
  tabelaExport
    .sort('pct_urbana_land', false)
    .select(PREVIEW_SELECTORS)
    .limit(10)
);
print(
  'Bairros com menor pct_lst_valid_land',
  tabelaExport
    .sort('pct_lst_valid_land', true)
    .select(PREVIEW_SELECTORS)
    .limit(10)
);

// ---------------------------------------------------------------------
// 8. Exportacao
// ---------------------------------------------------------------------

Export.table.toDrive({
  collection: tabelaExport,
  description: EXPORT_NAME,
  folder: EXPORT_FOLDER,
  fileNamePrefix: EXPORT_NAME,
  fileFormat: 'CSV',
  selectors: EXPORT_SELECTORS
});
