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

var tiles = [
    'tiles/2015-08-01T11:11:27.532711.png',
    'tiles/2015-08-01T11:21:28.098021.png',
    'tiles/2015-08-01T11:31:28.697978.png',
    'tiles/2015-08-01T11:41:28.864227.png',
    'tiles/2015-08-01T11:51:29.076501.png',
    'tiles/2015-08-01T12:01:29.293117.png',
    'tiles/2015-08-01T12:11:29.469843.png',
    'tiles/2015-08-01T12:21:29.648090.png',
    'tiles/2015-08-01T12:31:30.231707.png',
    'tiles/2015-08-01T12:41:30.415173.png',
];

var overlay = L.imageOverlay(tiles[0], bounds)
    .addTo(map);

var tile = 0;
setInterval(function() {
    console.log(tiles[tile % tiles.length]);
    overlay.setUrl(tiles[tile % tiles.length]);
    tile += 1;
}, 1000)
