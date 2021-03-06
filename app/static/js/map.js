
var chart;

const today = new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate());
const sensorDates = new Object({
  "Jason1": {"start":"2002-01-01","end":"2009-01-01"},
  "Jason2": {"start":"2008-07-04","end":"2017-07-01"},
  "Jason3": {"start":"2016-02-12","end":today},
  "Saral": {"start":"2016-02-12","end":today}
})

$(function(){

  mapboxgl.accessToken = 'pk.eyJ1Ijoia20wMDMzIiwiYSI6ImNrOWFsMmw3eDA0cm8zbWxrczB4OXA2OWUifQ.0NUvgcQYupWVsnu2vB974A';
  var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/light-v10',
    zoom: 4,
    center: [100,15],
    minZoom: 2,
    maxZoom: 14
  });

  map.on('load', function() {
    map.addSource('jrc-tiles', {
      'type': 'raster',
      'url': 'mapbox://km0033.jrctiles',
      'tileSize': 256,
      'attribution':
      'Map Data © <a target="_blank" rel="noopener" href="https://ec.europa.eu/info/departments/joint-research-centre_en">EC JRC</a>, ' +
      '<a target="_blank" rel="noopener" href="https://earthengine.google.com">Google Earth Engine</a>'
    });
    map.addLayer({
      'id': 'jrc-layer',
      'type': 'raster',
      'source': 'jrc-tiles',
    });

    // load the Jason ground tracks from tileset
    map.addSource('jason_groundtracks', {
      'type': 'vector',
      'url': 'mapbox://km0033.ck9xayqc601gj2kqaifekwpaw-6kkbo'
    });
    map.addLayer({
      'id': 'jason-layer',
      'type': 'line',
      'source': 'jason_groundtracks',
      'source-layer':'jason_groundtracks',
      'paint': {
        'line-color': '#1f77b4',
        'line-width': 2
      }
    });

    // load the SARAL ground tracks from tileset
    map.addSource('saral_groundtracks', {
      'type': 'vector',
      'url': 'mapbox://km0033.ck9xb3lfi01om2jqa3xkq2l2c-7mohd'
    });
    map.addLayer({
      'id': 'saral-layer',
      'type': 'line',
      'source': 'saral_groundtracks',
      'source-layer':'saral_groundtracks',
      'paint': {
        'line-color': '#9467bd',
        'line-width': 2
      }
    });
    map.setLayoutProperty('saral-layer', 'visibility', 'none');

  });

  var Draw = new MapboxDraw();

  // Map#addControl takes an optional second argument to set the position of the control.
  // If no position is specified the control defaults to `top-right`. See the docs
  // for more details: https://www.mapbox.com/mapbox-gl-js/api/map#addcontrol

  map.addControl(Draw, 'top-right');

  var iniStart = sensorDates['Jason2']['start'], iniEnd = sensorDates['Jason2']['end']
  buildDatepickers(iniStart,iniEnd,iniStart,iniEnd)

  $('#start-datepicker, #end-datepicker').on("change",function(){
    var dates = getDates()
    var start = Date.parse(dates[0]), end = Date.parse(dates[1])

    console.log(start,end)

    for (sensor in sensorDates) {
      var startAvail = Date.parse(sensorDates[sensor]['start'])
      var endAvail = Date.parse(sensorDates[sensor]['end'])

      var op = document.getElementById("satellite-selection").getElementsByTagName("option");

      if (end < startAvail || start > endAvail) {
        console.log("disabling selector for " + sensor)
        // for (i in op){
        //   if (op[i] == sensor) {
        //     console.log(op[i])
        //     op[i].disabled = true;
        //   }
        // }
        // $(`#satellite-selection option[value="${sensor}"]`).prop('disabled', true);
        $(`#satellite-selection option[value="${sensor}"]`).prop("disabled", true);
      }
    }
    $('#satellite-selection').selectpicker('refresh');

  })

  $("#app-nav-btn").on("click",function() {
    var $icon = $("#app-nav-btn-icon")
    var iconClass = $icon.attr('class')
    console.log()
    if (iconClass.includes("minus")) {
      $icon.removeClass("fas fa-minus")
      $icon.addClass("fas fa-plus")
      $("#app-nav-btn").removeClass("btn-outline-danger")
      $("#app-nav-btn").addClass("btn-outline-primary")

      $("#control-container").css("height","50px")
      $("#control-container").css("overflow-y","hidden")
    }
     else if (iconClass.includes("plus")) {
       $icon.removeClass("fas fa-plus")
       $icon.addClass("fas fa-minus")
       $("#app-nav-btn").removeClass("btn-outline-primary")
       $("#app-nav-btn").addClass("btn-outline-danger")

       $("#control-container").css("height","calc(100% - 155px)")
       $("#control-container").css("overflow-y","auto")
     }
  })

  $("#satellite-selection").on("change",function() {
    var sensorName = $(this).val()

    var dates = getDates()
    var start = dates[0], end = dates[1]
    $('#start-datepicker').datepicker('destroy');
    $('#end-datepicker').datepicker('destroy');

    var dateLookup = sensorDates[sensorName]
    if (start === ''){
      start = dateLookup['start']
    }
    if (end === '') {
      end = dateLookup['end']
    }
    buildDatepickers(new Date(dateLookup['start']),new Date(dateLookup['end']),start,end);

    if (sensorName.includes('Jason')){
      map.setLayoutProperty('jason-layer', 'visibility', 'visible');
      map.setLayoutProperty('saral-layer', 'visibility', 'none');
    }
    else if (sensorName.includes('Saral')) {
      map.setLayoutProperty('jason-layer', 'visibility', 'none');
      map.setLayoutProperty('saral-layer', 'visibility', 'visible');
    }
  });

  $("#rawdata-btn").on("click",function() {

    var sensor = $("#satellite-selection").val()

    var dates = getDates()
    var start = dates[0], end = dates[1]

    if (start == '' || end == ''){
      alert("Please provide a start and/or end time")
      return
    }

    var features = Draw.getAll()
    if (features.features.length ==0) {
      alert("Please draw a geometry to select data")
    }
    else if (features.features.length > 1) {
      alert("Please draw only one geometry")
      return
    } else {
      regionStr = constructGeomString(features)
    }
    var payload = {startTime:start,endTime:end,sensor:sensor,region:regionStr}

    //Destroy the old Datatable if it exists
    if ($.fn.dataTable.isDataTable('#table')) {
      $('#table').DataTable().clear().destroy();
    }

    // show the modal
    $('#tableModal').modal('toggle')
    // show the loader
    $('#tableLoader').toggle()

    $.ajax({
      type: 'GET',
      url: '/api/getTable',
      dataType: "json",
      data: payload,
      success: function(data){
        // turn of loader
        $('#tableLoader').toggle()

        var result = JSON.parse(data.result)
        if (result['data'].length === 0){
          alert ("Selection returned no data, please refine space and time parameters")
          $('#tableModal').modal('toggle')
          return
        }
        // get the result column information into a format for Datatables
        var header = []
        for (i in result['columns']){
          header.push({'title':result['columns'][i]})
        }
        // format the epoch time value to a datetime string
        for (i in result['data']){
          var d = new Date(result['data'][i][0])
          result['data'][i][0] = d.toString("yyyy-MM-dd HH:mm:ss.")+d.getMilliseconds().toString();
        }
        // write data to a fresh Datatable
        $('#table').DataTable({
          data: result['data'],
          columns: header,
          footer: header,
          dom: 'Blfrtip',
          buttons: ['copyHtml5', 'csvHtml5'],
          scrollX: true,

        });
      },
      error: function(data) {
        $('#tableLoader').toggle()
        alert(data.error)
      }
    });
  })

  $("#timeseries-btn").on("click",function() {

    var sensor = $("#satellite-selection").val()

    var filter = $("#filterCheck").is(":checked")

    var dates = getDates()
    var start = dates[0], end = dates[1]

    if (start == '' || end == ''){
      alert("Please provide a start and/or end time")
      return
    }

    var features = Draw.getAll()
    if (features.features.length == 0) {
      alert("Please draw a geometry to select data")
    }
    else if (features.features.length > 1) {
      alert("Please draw only one geometry")
      return
    } else {
      regionStr = constructGeomString(features)
    }
    var payload = {startTime:start,endTime:end,sensor:sensor,region:regionStr,applyFilter:filter}

    if (chart != null ) {
      try {
        chart.destroy()
      }
      catch(err) {
        chart = null
        console.log(err.message);
      }
    }

    // show the modal
    $('#chartModal').modal('toggle')
    // show the loader
    $('#chartLoader').toggle()

    $.ajax({
      type: 'GET',
      url: '/api/getWaterLevel',
      dataType: "json",
      data: payload,
      success: function(data){
        // turn of loader
        $('#chartLoader').toggle()
        var result = JSON.parse(data.result)
        if (result['data'].length === 0){
          alert ("Selection returned no data, please refine space and time parameters")
          return
        }
        var chartSeries = result['index'].map(function(v, i) {
          return [v, result['data'][i]];
        });
        chart = Highcharts.chart('chart', {
          title: {
            text: ''
          },
          yAxis: {
            title: {
              text: 'Height Above Reference Ellipsoid [m]'
            }
          },
          xAxis: {
            type: 'datetime',
            dateTimeLabelFormats: { // don't display the dummy year
                month: '%e. %b',
                year: '%b'
            },
            title: {
                text: 'Date'
            }
          },
          series: [{'name':'Water Level',data:chartSeries}],
          exporting: {
            enabled: true
          },
          credits: {
            enabled: false
          },
          legend: {
              enabled: false
          },
          plotOptions: {
            area: {
              fillColor: {
                linearGradient: {
                  x1: 0,
                  y1: 0,
                  x2: 0,
                  y2: 1
                },
                stops: [
                  [0, Highcharts.getOptions().colors[0]],
                  [1, Highcharts.color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
                ]
              },
              marker: {
                radius: 2
              },
              lineWidth: 1,
              states: {
                hover: {
                  lineWidth: 1
                }
              },
              threshold: null
            }
          },
        })
      },
      error: function(data) {
        $('#chartLoader').toggle()
        alert(data.error)
      }
    });
  })

  $("#close-data").on("click", function() {
    $('#exampleModal').modal('toggle')
  })
  $("#close-chart").on("click", function() {
    $('#exampleModal').modal('toggle')
  })
// end main function
})

function constructGeomString(features){
  var regionStr = ''
  var coords = features.features[0].geometry.coordinates[0]
  var nVertices = coords.length
  for (i in coords) {
    var vertex = coords[i][0].toString().slice(0,7) + ' ' + coords[i][1].toString().slice(0,7)
    if (i != nVertices-1){
      vertex += ','
    }
    regionStr += vertex
  }
  return regionStr
}

function buildDatepickers(minDate,maxDate,defaultStart,defaultEnd){
   $startpicker = $('#start-datepicker').datepicker({
    uiLibrary: 'bootstrap4',
    format: 'yyyy-mm-dd',
    minDate: minDate,
    maxDate: function () {
      if ($('#endDate').val()) {
        return $('#endDate').val();
      }
      else {
        return maxDate
      }
    }
  });
  $startpicker.value(defaultStart);

  $endpicker = $('#end-datepicker').datepicker({
    uiLibrary: 'bootstrap4',
    format: 'yyyy-mm-dd',
    defaultDate: defaultEnd,
    maxDate: maxDate,
    minDate: function () {
      return $('#start-datepicker').val();
    }
  });
  $endpicker.value(defaultEnd);
}

function getDates() {
  var start = $('#start-datepicker').val()
  var end = $('#end-datepicker').val()
  return [start,end]
}
