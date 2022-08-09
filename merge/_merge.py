from functools import reduce

import pandas as pd
import numpy as np

from ._ast import AST

_LENGTH_LEFT  = "__LEFT_LENGTH__"
_LENGTH_RIGHT = "__RIGHT_LENGTH__"

def merge_on_intervals(
    left_data     : pd.DataFrame,
    right_data    : pd.DataFrame,
    join_left_on  : list[str],
    from_to       : tuple[str, str],
    add_columns   : list[AST]
):
    from_column, to_column = from_to

    # plan executions
    add_columns_planned = [AST.optimize(myast) for myast in add_columns]
    
    # determine the columns needed for the body of the algorithm
    left_columns_needed, right_columns_needed = reduce(
        lambda a,b: ({*a[0], *b[0]}, {*a[1],*b[1]}),
        [AST.columns_required(myast) for myast in add_columns]
    )

    # determine the resulting column names

    result_column_names = [AST.output_column_name_simple(myast) for myast in add_columns]

    # keep the original left data, but with the index reset
    left_data_original = left_data.reset_index(drop=True)

    # select only the relevant columns
    left_data   = left_data .loc[:,list({*join_left_on, *from_to, *left_columns_needed })].reset_index(drop=True)
    right_data  = right_data.loc[:,list({*join_left_on, *from_to, *right_columns_needed})].reset_index(drop=True)

    # compute lengths
    left_data [_LENGTH_LEFT ] = left_data [to_column] - left_data [from_column]
    right_data[_LENGTH_RIGHT] = right_data[to_column] - right_data[from_column]

    # group data for left join
    left_groups  = left_data .groupby(by=join_left_on)
    right_groups = right_data.groupby(by=join_left_on)

    left_group :pd.DataFrame
    right_group:pd.DataFrame
    
    # prepare list to store output
    result_index = []
    result_rows = []

    for group_index, left_group in left_groups:
        right_group = right_groups.get_group(group_index)
        for left_row_index, left_row in left_group.iterrows():
            
            # compute signed overlap
            overlap_min = np.maximum(left_row[from_column], right_group[from_column])
            overlap_max = np.minimum(left_row[to_column  ], right_group[to_column  ])
            signed_overlap_len = overlap_max - overlap_min
            
            result_index.append(left_row_index)
            result_rows.append([
                AST.evaluate(
                    myast,
                    left_columns      = left_row,
                    right_columns     = right_group,
                    length_of_left    = left_row[_LENGTH_LEFT],
                    length_of_right   = right_group[_LENGTH_RIGHT],
                    length_of_overlap = signed_overlap_len
                )
                for myast in add_columns_planned
            ])
    return pd.concat(
        [
            left_data_original,
            pd.DataFrame(
                columns = result_column_names,
                index   = result_index,
                data    = result_rows,
            )
        ],
        axis="columns"
    )