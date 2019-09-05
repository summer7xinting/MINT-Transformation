#!/usr/bin/python
# -*- coding: utf-8 -*-

from ccut.app.ccut_lib import CCUT, RET_VAL_OK, RET_STR_MAP
from dtran.argtype import ArgType, Optional
from dtran.ifunc import IFunc
from drepr import Graph


class UnitTransFunc(IFunc):
    id = "unit_trans"
    inputs = {
        "graph": ArgType.Graph(None),
        "unit_value": ArgType.String,
        "unit_label": ArgType.String,
        "unit_desired": ArgType.String,
        "filter": ArgType.String(True),
    }
    outputs = {"graph": ArgType.Graph(None)}

    def __init__(
        self, graph: Graph, unit_value: str, unit_label: str, unit_desired: str, filter: Optional[str] = None
    ):
        self.graph = graph
        self.unit_value = unit_value
        self.unit_label = unit_label
        self.unit_desired = unit_desired
        self.filter_func = IFunc.filter_func(filter)
        self.ccut = CCUT()

    def exec(self):
        for node in self.graph.nodes:
            if self.filter_func(node):
                print(node)
                src_unit = node.data[self.unit_label]
                conversion_value, err_code = self.ccut.canonical_transform(src_unit, self.unit_desired, 1)
                if RET_VAL_OK != err_code:
                    raise ValueError(
                        f"Error in the unit conversion process['{src_unit}' --> '{self.unit_desired}']: [{err_code}] "
                        f"{RET_STR_MAP[err_code]}"
                    )
                new_obs_value = float(node.data[self.unit_value]) * conversion_value
                node.data[self.unit_value] = str(new_obs_value)
                node.data[self.unit_label] = self.unit_desired
                print(node)
        return {"graph": self.graph}
