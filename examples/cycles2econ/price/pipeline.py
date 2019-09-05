import os
from pathlib import Path

from dtran import Pipeline
from funcs import ReadFunc, GraphWriteFunc, UnitTransFunc, GraphStr2StrFunc
from funcs.write_func import VisJsonWriteFunc

if __name__ == "__main__":
    wdir = Path(os.path.abspath(__file__)).parent
    crop_names = {
        "Maize (white) - Retail": "maize",
        "Cassava - Retail": "cassava",
        "Groundnuts (shelled) - Retail": "groundnuts",
        "Sesame - Retail": "sesame",
        "Sorghum (white, imported) - Retail": "sorghum",
    }

    pipeline = Pipeline(
        [ReadFunc, UnitTransFunc, GraphWriteFunc, VisJsonWriteFunc],
        wired=[
            ReadFunc.O.data == UnitTransFunc.I.graph,
            UnitTransFunc.O.graph == GraphWriteFunc.I.graph,
            UnitTransFunc.O.graph == VisJsonWriteFunc.I.graph,
        ],
    )

    inputs = {
        ReadFunc.I.repr_file: wdir / "wfp_food_prices_south-sudan.repr.yml",
        ReadFunc.I.resources: wdir / "wfp_food_prices_south-sudan.csv",
        # GraphStr2StrFunc.I.semantic_type: "qb:Observation--dcat-dimension:thing",
        # GraphStr2StrFunc.I.str2str: ujson.dumps(crop_names),
        UnitTransFunc.I.filter: "@type = 'qb:Observation' and "
        "sdmx-attribute:refArea.contains('Aweil (Town)') and "
        "sdmx-dimension:refPeriod = '2016-10-15' and "
        f"dcat-dimension:thing in {str(set(crop_names.keys()))}",
        UnitTransFunc.I.unit_value: "dcat:measure_1_value",
        UnitTransFunc.I.unit_label: "sdmx-attribute:unitMeasure",
        UnitTransFunc.I.unit_desired: "$/kg",
        GraphWriteFunc.I.main_class: "qb:Observation",
        GraphWriteFunc.I.mapped_columns: {},
        GraphWriteFunc.I.output_file: wdir / "price.csv",
        VisJsonWriteFunc.I.main_class: "qb:Observation",
        VisJsonWriteFunc.I.mapped_columns: {},
        VisJsonWriteFunc.I.output_file: wdir / "visualization.json",
    }

    outputs = pipeline.exec(inputs)
