from datasources.owl import get_bto_ontology

import pandas as pd
from owlready2 import (
    owl,
    Restriction,
    ThingClass,
)


def get_tissue_nodes_df():
    onto = get_bto_ontology()
    rows_list = [
        { 'bto_id': c.name, 'name': c.label.first() }
        for c in onto.classes()
    ]
    return pd.DataFrame(rows_list, columns=['bto_id'])


def get_tissue_edges():
    onto = get_bto_ontology()
    rows_list = []

    for bto_obj in onto.classes():
        for bto_parent_class in set(bto_obj.is_a):
            # Ignore the root/parent class
            if bto_parent_class == owl.Thing:
                continue
            else:
                bto_obj_type = type(bto_parent_class)
                if bto_obj_type == ThingClass:
                    rows_list.append({
                        'bto_id': bto_obj.name,
                        'parent_bto_id': bto_parent_class.name,
                    })
                elif bto_obj_type == Restriction:
                    # Restriction 2202 defines a derives_from/develops_from relationship
                    rows_list.append({
                        'bto_id': bto_obj.name,
                        'parent_bto_id': bto_parent_class.value.name,
                    })
    return pd.DataFrame(rows_list, columns=['bto_id', 'parent_bto_id'])