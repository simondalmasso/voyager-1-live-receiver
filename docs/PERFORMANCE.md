# Performance

The runtime has no third-party JavaScript, textures, fonts, or binary model. The build report enforces an initial local asset budget under 6 MB; expected output is far smaller. WebGL uses one procedural triangle buffer, one star point buffer, and bounded line buffers. DPR is capped, no React state or DOM update occurs per frame, and the signal waterfall has fixed rows/bins. Hidden-tab pausing remains a future optimization if measured necessary.
