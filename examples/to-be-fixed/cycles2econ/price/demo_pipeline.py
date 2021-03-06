import os
from pathlib import Path
from urllib import request

from examples.cycles2econ.price.dcat_api import DCatAPI

from dtran import Pipeline
from funcs import ReadFunc, CSVWriteFunc, UnitTransFunc
from funcs.writers.write_func import VisJsonWriteFunc

if __name__ == "__main__":
    id = "9e0de813-9b6b-4871-99f5-902b8c1aa26c"

    dcat_api = DCatAPI.get_instance()

    resources = dcat_api.find_resources_by_dataset_id("", id)
    drepr = resources['dataset']['metadata']['layout']
    wdir = Path(os.path.abspath(__file__)).parent

    request.urlretrieve(resources["data_url"], wdir / 'wfp_food_prices_south-sudan.csv')

    crop_names = {
        "Maize (white) - Retail": "maize",
        "Cassava - Retail": "cassava",
        "Groundnuts (shelled) - Retail": "groundnuts",
        "Sesame - Retail": "sesame",
        "Sorghum (white, imported) - Retail": "sorghum",
    }

    pipeline = Pipeline(
        [ReadFunc, UnitTransFunc, CSVWriteFunc, VisJsonWriteFunc],
        wired=[
            ReadFunc.O.data == UnitTransFunc.I.graph,
            UnitTransFunc.O.graph == CSVWriteFunc.I.graph,
            UnitTransFunc.O.graph == VisJsonWriteFunc.I.graph,
        ],
    )

    inputs = {
        ReadFunc.I.repr_file: wdir / "wfp_food_prices_south-sudan.repr.yml",
        ReadFunc.I.resources: wdir / "wfp_food_prices_south-sudan.csv",
        # GraphStr2StrFunc.I.semantic_type: "qb:Observation--dcat-dimension:thing",
        # GraphStr2StrFunc.I.str2str: ujson.dumps(crop_names),
        UnitTransFunc.I.unit_value: "dcat:measure_1_value",
        UnitTransFunc.I.unit_label: "sdmx-attribute:unitMeasure",
        UnitTransFunc.I.unit_desired: "$/kg",
        CSVWriteFunc.I.main_class: "qb:Observation",
        CSVWriteFunc.I.mapped_columns: {},
        CSVWriteFunc.I.output_file: wdir / "price.csv",
        VisJsonWriteFunc.I.filter: "@type = 'qb:Observation' and "
                                   "sdmx-attribute:refArea.contains('Aweil (Town)') and "
                                   "sdmx-dimension:refPeriod = '2016-10-15' and "
                                   f"dcat-dimension:thing in {str(set(crop_names.keys()))}",
        VisJsonWriteFunc.I.main_class: "qb:Observation",
        VisJsonWriteFunc.I.mapped_columns: {},
        VisJsonWriteFunc.I.output_file: wdir / "visualization.json",
    }

    outputs = pipeline.exec(inputs)
