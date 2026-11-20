"""Build simplified state and dissolved 5-region GeoJSON for the dashboard map.
Source: github.com/datta07/INDIAN-SHAPEFILES (INDIA/INDIA_STATES.geojson, Survey-of-India-based boundaries).
Polygons are re-oriented clockwise (exterior) as d3-geo / Plotly expect."""
import json
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from src.config import RAW, PROC

NAME_TO_REGION = {
    "NR": ["DELHI", "HARYANA", "HIMACHAL PRADESH", "JAMMU & KASHMIR", "LADAKH", "PUNJAB", "RAJASTHAN", "UTTAR PRADESH", "UTTARAKHAND", "CHANDIGARH"],
    "WR": ["GUJARAT", "MAHARASHTRA", "MADHYA PRADESH", "CHHATTISGARH", "GOA", "DADRA & NAGAR HAVELI", "DAMAN & DIU"],
    "SR": ["ANDHRA PRADESH", "TELANGANA", "KARNATAKA", "KERALA", "TAMIL NADU", "PUDUCHERRY", "LAKSHADWEEP"],
    "ER": ["BIHAR", "JHARKHAND", "ODISHA", "WEST BENGAL", "SIKKIM", "ANDAMAN & NICOBAR"],
    "NER": ["ARUNACHAL PRADESH", "ASSAM", "MANIPUR", "MEGHALAYA", "MIZORAM", "NAGALAND", "TRIPURA"]}
ST2R = {s: r for r, l in NAME_TO_REGION.items() for s in l}


def _cw(geom):
    if isinstance(geom, Polygon):
        return orient(geom, sign=-1.0)
    if isinstance(geom, MultiPolygon):
        return MultiPolygon([orient(p, sign=-1.0) for p in geom.geoms])
    return geom


def _rnd(o):
    if isinstance(o, float):
        return round(o, 3)
    if isinstance(o, (list, tuple)):
        return [_rnd(x) for x in o]
    if isinstance(o, dict):
        return {k: _rnd(v) for k, v in o.items()}
    return o


def build(tol=0.02):
    g = json.load(open(RAW / "india_states_datta07.geojson"))
    sf, rg = [], {r: [] for r in NAME_TO_REGION}
    for f in g["features"]:
        nm = f["properties"]["STNAME"]
        geo = shape(f["geometry"]).buffer(0)
        sf.append({"type": "Feature", "id": nm, "properties": {"state": nm, "region": ST2R[nm]},
                   "geometry": mapping(_cw(geo.simplify(tol, preserve_topology=True)))})
        rg[ST2R[nm]].append(geo)
    rf = [{"type": "Feature", "id": r, "properties": {"region": r},
           "geometry": mapping(_cw(unary_union(l).simplify(tol, preserve_topology=True)))} for r, l in rg.items()]
    json.dump(_rnd({"type": "FeatureCollection", "features": sf}), open(PROC / "india_states_simplified.geojson", "w"))
    json.dump(_rnd({"type": "FeatureCollection", "features": rf}), open(PROC / "india_grid_regions.geojson", "w"))
    print("[geo] state + region GeoJSON written")


if __name__ == "__main__":
    build()
