from ._ast import AST
import pandas as pd

def on_intervals(
    left_data     : pd.DataFrame,
    right_data    : pd.DataFrame,
    join_left_on  : list[str],
    from_to       : tuple[str, str],
    add_columns   : list[AST]
):
    # TODO: type checking
    # TODO: column presents and overlap testing etc

    columns_needed_from_data = {AST.columns_required for ast in add_columns}

    left_data   = left_data .loc[:,[*join_left_on,*from_to]].reset_index(drop=True)
    right_data  = right_data.loc[:,[*join_left_on,*from_to]].reset_index(drop=True)
