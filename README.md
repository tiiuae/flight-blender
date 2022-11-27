<img src="images/blender-logo.jfif" width="350">

# Flight Blender

Flight Blender enables you to be compliant with latest regulations on UTM / U-Space in the EU. It gives you:

- an open source Remote ID "display provider" compatible with ASTM Remote ID standard
- an open source implementation of the ASTM USS <-> USS standard and compatible with the EU U-Space regulation for flight authorisation
- ability to consume geo-fences per the ED-269 standard
- a flight traffic feed aggregator that has different modules that can process and relay data around flights and airspace: geo-fence, flight declarations, air-traffic data.

There are different modules that enable this:

- _DSS Connectivity_: There are modules to connect and read for e.g. Remote ID data from a DSS, Strategic deconfliction / flight authorization
- _Flight Tracking_: It takes in flight tracking feeds from various sources e.g. ADS-B, live telemetry, Broadcast Remote ID and others and outputs as a single fused JSON feed and submits it to a Display Application e.g. [Flight Spotlight](https://github.com/openskies-sh/flight-spotlight) to be shown in real-time on a display
- _Geofence_: A Geofence can be submitted into Flight Blender and consequently transmitted to Spotlight
- _Flight Declaration_: Future flights up-to 24 hours can be submitted, this support both the ASTM USS <-> USS API and can also be used as a standalone component, for supported DSS APIs see below

## Openskies stack

To visualize flight tracking data you can use a complementary appplication like [Flight Spotlight](https://github.com/openskies-sh/flight-spotlight). To submit data like Geofences etc. into Flight Blender beyond the API you can use the user interface provided by Spotlight, for more information see the diagram below.

![OpenskiesStack](images/openskies-stack.png)

## Installation

**NB**s: Flight Blender __will__ require a authorization server to work, we normally make credentials available via [Openskies ID](https://id.openskies.sh), please contact us via the home page to get your credentials for self-hosting.

Docker and Docker Compose files are available for this software. You can first clone this repository using `git clone https://www.github.com/openskies-sh/flight-blender.git` and then go to the directory and use `docker-compose up` command.

This will open up port 8080 and you can post air-traffic data to `http://localhost:8080/set_air_traffic` and then start the processing.

## Technical details

- To begin, review the [API Specification](http://redocly.github.io/redoc/?url=https://raw.githubusercontent.com/openskies-sh/flight-blender/master/api/flight-blender-1.0.0-resolved.yaml) to understand the endpoints and the kind of data that you can set in Flight Blender.
- Then take a look at some data formats: [Flight tracking data](https://github.com/openskies-sh/flight-blender/blob/master/importers/air_traffic_samples/micro_flight_data_single.json). This file follows the format as specified in the [Air-traffic data protocol](https://github.com/openskies-sh/airtraffic-data-protocol-development/blob/master/Airtraffic-Data-Protocol.md)

## Submitting AOI, Flight Declarations and Geofence data

Take a look at sample data below to see the kind of data that can be submitted in Flight Blender

- [Area of Interest](https://github.com/openskies-sh/flight-blender/blob/master/importers/aoi_geo_fence_samples/aoi.geojson) as a GeoJSON
- [Geofence](https://github.com/openskies-sh/flight-blender/blob/master/importers/aoi_geo_fence_samples/geo_fence.geojson) as a GeoJSON, we have converters to convert EuroCAE from ED-269 standard
- [Flight Declaration](https://github.com/openskies-sh/flight-blender/blob/master/importers/flight_declarations_samples/flight-1.json). This file follows the format specified in [Flight Declaration Protocol](https://github.com/openskies-sh/flight-declaration-protocol-development), optionally when using DSS components it supports "operational intent" APIs.

## Image Credit

<a href="https://www.vecteezy.com/free-vector/blender">Blender Vectors by Vecteezy</a>
