
mapboxgl.accessToken = 'pk.eyJ1Ijoia20wMDMzIiwiYSI6ImNrOWFsMmw3eDA0cm8zbWxrczB4OXA2OWUifQ.0NUvgcQYupWVsnu2vB974A';
var map = new mapboxgl.Map({
  container: 'map',
  style: 'mapbox://styles/mapbox/light-v10',
  zoom: 4,
  center: [100,15]
});

var Draw = new MapboxDraw();

// Map#addControl takes an optional second argument to set the position of the control.
// If no position is specified the control defaults to `top-right`. See the docs
// for more details: https://www.mapbox.com/mapbox-gl-js/api/map#addcontrol

map.addControl(Draw, 'top-right');

map.on('load', function() {
  // load the Jason ground tracks from tileset
  map.addSource('jason-groundtrack', {
    'type': 'vector',
    'url': 'mapbox://km0033.ck9ajcalw05jn2smyb9jnjgd8-94d4w'
  });

  map.addLayer({
    'id': 'jason-layer',
    'type': 'line',
    'source': 'jason-groundtrack',
    'source-layer':'jason_groundtrack',
    'paint': {
      'line-color': '#1f77b4',
      'line-width': 2
    }
  });

  // load the SARAL ground tracks from tileset
  map.addSource('saral-groundtrack', {
    'type': 'vector',
    'url': 'mapbox://km0033.62y2lfui'
  });

  map.addLayer({
    'id': 'saral-layer',
    'type': 'line',
    'source': 'saral-groundtrack',
    'source-layer':'saral-6qwbu7',
    'paint': {
      'line-color': '#9467bd',
      'line-width': 2
    }
  });


});


$('#start-datepicker').datepicker({
        uiLibrary: 'bootstrap4'
    });
$('#end-datepicker').datepicker({
        uiLibrary: 'bootstrap4'
    });
