from django.urls import path

from . import views as geo_fence_views

urlpatterns = [
    path("set_geo_fence", geo_fence_views.set_geo_fence, name="set_geo_fence"),
    path("set_geozone", geo_fence_views.set_geozone),
    path("geo_fence", geo_fence_views.GeoFenceList.as_view()),
    path("geo_fence/<uuid:pk>", geo_fence_views.GeoFenceDetail.as_view()),
    # End points for automated testing interface
    path("geo_awareness/status", geo_fence_views.GeoZoneTestHarnessStatus.as_view()),
    path(
        "geo_awareness/geozone_sources/<uuid:geozone_source_id>",
        geo_fence_views.GeoZoneSourcesOperations.as_view(),
    ),
    path("geo_awareness/geozones/check", geo_fence_views.GeoZoneCheck.as_view()),
]
