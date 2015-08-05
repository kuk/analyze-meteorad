$.getJSON("tiles.json", function(data) {
    var tiles = [];
    $.each(data, function(timestamp, path) {
	tiles.push({
	    label: timestamp.slice(-5),
	    timestamp: timestamp,
	    path: path
	});
    });
    tiles.sort(function(left, right) {
	return left.timestamp.localeCompare(right.timestamp);
    });
    tiles = tiles.slice(-12);
    
    L.mapbox.accessToken = 'pk.eyJ1IjoiYWxleGt1ayIsImEiOiJlOWVlZmExMGFiMmVkNzBiM2NlYmMzM2I3YTViZTEwOSJ9.aWcWknXEzB7U9z0fARBTiA';

    bounds = L.latLngBounds([
	[57.69164752, 33.13470459],
	[53.33323917, 41.44036865],
    ]);

    var map = L.mapbox.map('map', 'mapbox.streets', {
	maxBounds: bounds,
	maxZoom: 11,
	minZoom: 8
    }).fitBounds(bounds);

    var overlay = L.imageOverlay(tiles[0], bounds)
	.addTo(map);

    function update(index) {
	var tile = tiles[index];
	$("#slider").find(".ui-slider-handle").text(tile.label);
	overlay.setUrl(tile.path);
    }

    var max = tiles.length - 1;
    $("#slider").slider({
	value: 0,
	min: 0,
	max: max,
	step: 1,
	slide: function(event, ui) {
	    update(ui.value);
	},
	change: function(event, ui) {
	    update(ui.value);
	}
    });

    update(0)
    var index = 0;
    setInterval(function() {
	if (index <= max) {
	    $("#slider").slider('value', index);
	    index += 1;
	}
    }, 1000);
});
