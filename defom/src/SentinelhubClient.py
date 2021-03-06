from sentinelhub import SHConfig
from shapely.geometry import shape
from sentinelhub import OsmSplitter, BBox, read_data, CRS, Geometry, SentinelHubRequest, DataCollection, MimeType, bbox_to_dimensions

class SentilhubClient(object):

    def __init__(self):
        config = SHConfig()
        self.config = config
        self.set_config()

        pass

    def set_config(self):
        if not self.config.sh_client_id or not self.config.sh_client_secret:
            self.config.instance_id = '34a08c5f-1cf6-4348-86e5-79ff3461bbc2'
            self.config.sh_client_id = '7dc75a0c-46bd-48f2-9719-da76511d5f01'
            self.config.sh_client_secret = "ZT*ao<H2~_7P[?@PZY:]t}[,D[A5!b7A^0v_LQf-"
            self.config.save()

    def split_forest_area(self, json_data):
        """
        INPUT:
            forest_map : TODO
        OUTPUT:
            list of BBOX objects in the form of [((lat1, lon1), (lat2, lon2)), ...]
        """
        forest_area = shape(json_data['features'][0]['geometry'])
        osm_splitter = OsmSplitter([forest_area], CRS.WGS84, zoom_level=12)
        bbox_list = osm_splitter.get_bbox_list()
        bbox_coords_list = []

        ind = 0
        for bbox in bbox_list:
            bbox_poly = bbox.get_polygon()
            bbox_coords_list.append({'tile_id' : ind, 'bbox':(bbox_poly[0], bbox_poly[2]), 'infered_threat_class':[]})
            ind+=1

        return bbox_coords_list

    def get_forest(self, geo_json, start_date, end_date):

        evalscript_true_color = """
            //VERSION=3
            function setup() {
                return {
                    input: [{
                        bands: ["B02", "B03", "B04"]
                    }],
                    output: {
                        bands: 3
                    }
                };
            }
            function evaluatePixel(sample) {
                return [sample.B04, sample.B03, sample.B02];
            }
        """
            
        full_geometry = Geometry(geo_json['features'][0]['geometry'], crs=CRS.WGS84)

        request = SentinelHubRequest(
            evalscript=evalscript_true_color,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(start_date, end_date),
                    mosaicking_order='leastCC'
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.PNG)
            ],
            geometry=full_geometry,
            size=(256, 256),
            config=self.config
        )
        image = request.get_data()[0]
        return image


    def get_tile(self, bbox_coords, resolution, start_date, end_date):
        """
        INPUT:
            bbox_coords : list of floats in format [lat1, lon1, lat2, lon2]
            resolution : res of the tile [int]
            start_date : start date to collect of given coordinates [String format : '2020-06-01']
            end_date : last date excluding to consider [same format as above]
        OUTPUT:
            png image 
        """
        tile_bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
        tile_size = bbox_to_dimensions(tile_bbox, resolution=resolution)

        evalscript_true_color = """
                //VERSION=3
                function setup() {
                return {
                    input: [{
                        bands: ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12"],
                        units: "DN"
                    }],
                    output: {
                        id: "default",
                        bands: 12,
                        sampleType: SampleType.UINT16
                    }
                }
                }

                function evaluatePixel(sample) {
                    return [ sample.B02, sample.B03, sample.B04, sample.B08, sample.B11]
                }
            """

        request_true_color = SentinelHubRequest(
            evalscript=evalscript_true_color,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L1C,
                    time_interval=(start_date, end_date),
                    mosaicking_order='leastCC'
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=tile_bbox,
            size=(242,242),
            config=self.config
        )
        true_color_imgs = request_true_color.get_data()
        return true_color_imgs


