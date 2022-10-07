from __future__ import annotations
from re import S
from typing import Any, Iterator, Literal, TypeVar, Union, Generator
import itertools
from xmlrpc.client import Boolean
import pandas as pd
from collections import deque

from ._util.nicks_itertools import is_last

Action = Literal[
    "left_column",
    "right_column",
    "+",
    "-",
    "*",
    "/",
    ">",
    "<",
    "==",
    "b_and",
    "b_or",
    "l_not",
    "neg",
    "fraction_of_right",
    "fraction_of_left",
    "length_of_left",
    "length_of_right",
    "length_of_overlap",
    "filter",
    "alias",
    "group_and_aggregate",
    "sum",
    "index_of_max",
    "at_index",
    "astype",
    "slice_integer",
    "slice_label",
    "declare",
    "refer",
    "execute",
    "logical_and",
    "logical_or",
    "logical_not",
    "isna",
    "hstack",
    "groupby"

]
ASTChild = Union["AST", float, int, bool, str, slice]

Path_Value = tuple[list[int], ASTChild]

class _AST_Slice_Maker:
    host:AST
    def __init__(self, host:AST) -> None:
        self.host = host
    def __getitem__(self, slicer:slice) -> AST:
        raise NotImplemented()

class _AST_Slice_Label_Maker(_AST_Slice_Maker):
    def __getitem__(self, slicer:slice) -> AST:
        return AST("slice_label",[self.host, slicer])

class _AST_Slice_Integer_Maker(_AST_Slice_Maker):
    def __getitem__(self, slicer:slice) -> AST:
        return AST("slice_integer",[self.host, slicer])

class AST:
    action:Action
    children:list[ASTChild]
    
    def __init__(self, action:Action, children:list[ASTChild]):
        self.action   = action
        self.children = children
        self.loc  = _AST_Slice_Label_Maker  (self)
        self.iloc = _AST_Slice_Integer_Maker(self)
    
    def __repr__(self):
        return f"⟨AST {self.action}" + (
            f" {self.children[0]}⟩"
            if len(self.children) == 1 and not isinstance(self.children[0], AST) 
            else "⟩"
        )

    def _to_string(self, indent:str="", is_parents_last=False)->str:
        if len(indent) != 0:
            modified_indent = indent[:-3]+" ┠╴"
            if is_parents_last:
                modified_indent = indent[:-3]+" ┖╴"
        else:
            modified_indent = indent
        

        out = f"\n{modified_indent}⟨{self.action}⟩"
        if len(self.children)>0:
            *children_tail, children_head = self.children
            for islast, child in is_last(iter(self.children)):
                if isinstance(child, AST):
                    out+=child._to_string(indent+(" ┃ " if not islast else "   "), islast)
                elif isinstance(child, str):
                    out+=f'\n{indent+(" ┖╴" if islast else " ┠╴")}"{child}"'
                else:
                    out+=f'\n{indent+(" ┖╴" if islast else " ┠╴")}{child}'
        return out

    def _to_string_print(self):
        print(self._to_string())
    
    def slice_label(self, slicer:ASTChild) -> AST:
        return AST("slice_label", [self, slicer])

    def slice_integer(self, slicer:ASTChild) -> AST:
        return AST("slice_integer", [self, slicer])

    def filter(self, other:AST) -> AST:
        return AST("filter", [self, other])

    def alias(self, other:str) -> AST:
        return AST("alias", [self, other])

    def group_and_aggregate(self, other:AST) -> AST:
        return AST("group_and_aggregate", [self, other])

    def __add__(self, other:ASTChild) -> AST:
        return AST("+",[self, other])

    def __sub__(self, other:ASTChild) -> AST:
        return AST("-",[self, other])

    def __mul__(self, other:ASTChild) -> AST:
        return AST("*",[self, other])

    def __truediv__(self, other:ASTChild) -> AST:
        return AST("/",[self, other])

    def __gt__(self, other:ASTChild) -> AST:
        return AST(">",[self, other])

    def __lt__(self, other:ASTChild) -> AST:
        return AST("<",[self, other])

    def __eq__(self, other:ASTChild) -> AST:
        return AST("==", [self, other])

    def __and__(self, other:ASTChild) -> AST:
        return AST("b_and", [self, other])

    def __or__(self, other:ASTChild) -> AST:
        return AST("b_or", [self, other])

    def __invert__(self) -> AST:
        return AST("l_not", [self])

    def __bool__(self):
        raise Exception(
            "Cannot use `and`, `not` and `or` because `PEP 335 - Overloadable Boolean Operators` was rejected.\n"
            "Yay for python.\n"
            "It was because the `and` and `or` operators have special short-circuit behavior;\n"
            "the second operand of `or` will never be evaluated if the first operand evaluates to true.\n"
            "This builtin behavior conflicts with our Abstract Syntax Tree building endeavour.\n"
            "Please use `AST.logical_and(a,b)`, `AST.logical_or(a,b)` or `AST.logical_not(a)`.\n"
            "Still, I think it was a bad decision."
        )
    
    def sum(self) -> AST:
        return AST("sum",[self])

    def isna(self) -> AST:
        return AST("isna",[self])

    def index_of_max(self) -> AST:
        return AST("index_of_max",[self])

    def at_index(self, idx:ASTChild) -> AST:
        return AST("at_index",[self, idx])

    def astype(self, typ:str) -> AST:
        return AST("astype",[self, typ])

    def groupby(self, grouper:ASTChild) -> AST:
        return AST("groupby",[self, grouper])


# ====================================================================================================================
#          MODULE METHODS
# ====================================================================================================================

def clone(myast:ASTChild) -> ASTChild:
    if not isinstance(myast, AST):
        return myast
    return AST(myast.action, [*map(clone, myast.children)])

def left_column(name:str) -> AST:
    return AST("left_column", [name])

def right_column(name:str) -> AST:
    return AST("right_column", [name])

def length_of_overlap() -> AST:
    return AST("length_of_overlap", [])

def fraction_of_right() -> AST:
    return AST("fraction_of_right", [])

def fraction_of_left() -> AST:
    return AST("fraction_of_left", [])

def length_of_left() -> AST:
    return AST("length_of_left", [])

def length_of_right() -> AST:
    return AST("length_of_right", [])

def logical_and(left:ASTChild, right:ASTChild)->AST:
    return AST("logical_and", [left, right])

def logical_or(left:ASTChild, right:ASTChild)->AST:
    return AST("logical_or", [left, right])

def logical_not(left:ASTChild)->AST:
    return AST("logical_not", [left])

def hstack(left:AST, right:AST) -> AST:
    return AST("hstack",[left,right])





def execute(statements:list[AST]) ->AST:
    return AST("execute", statements)


def declare(name:str, value:ASTChild) -> AST:
    return AST("declare", [name, value])


def refer(name:str) -> AST:
    return AST("refer", [name])


def evaluate(
    myast:AST,
    left_columns      :pd.Series,    # one row of the left dataframe, as a series where the index are the column names of the left dataframe
    length_of_left    :float,
    right_columns     :pd.DataFrame,
    length_of_right   :pd.Series,
    length_of_overlap :pd.Series,
):
    
    context:dict[str,Any] = {}

    def walker(myast:ASTChild):

        nonlocal right_columns
        nonlocal left_columns
        nonlocal length_of_left
        nonlocal right_columns
        nonlocal length_of_right
        nonlocal length_of_overlap

        nonlocal context

        if not isinstance(myast, AST):
            return myast

        if myast.action == "left_column":
            return left_columns[myast.children[0]]

        if myast.action == "right_column":
            return right_columns[myast.children[0]]
        
        if myast.action == "length_of_overlap":
            return length_of_overlap
        
        if myast.action == "length_of_left":
            return length_of_left
        
        if myast.action == "length_of_right":
            return length_of_right
        
        if myast.action == "fraction_of_left":
            return length_of_left / length_of_overlap
        
        if myast.action == "fraction_of_right":
            return length_of_right / length_of_overlap

        # walk children in advance to help with future error checking            
        walker_children = [walker(child) for child in myast.children]

        if myast.action == "filter":
            series, mask = walker_children
            # todo: the checks below are not good
            if not isinstance(series, (pd.Series, pd.DataFrame)):
                raise Exception(f"Unable to filter object {series} that is not a Series or DataFrame")
            if not mask.dtype == bool:
                raise Exception(f"Filter mask is not a boolean series {mask}")
            return series.loc[mask]

        if myast.action == "sum":
            #if not isinstance(walker_children[0], (pd.Series, pd.DataFrame, pd.Gro)):
            #    raise Exception(f"Unable to sum object {walker_children[0]} which is not Series or DataFrame")
            return walker_children[0].sum()

        if myast.action == "+":
            return walker_children[0] + walker_children[1]
        
        if myast.action == "-":
            return walker_children[0] - walker_children[1]

        if myast.action == "*":
            return walker_children[0] * walker_children[1]
        
        if myast.action == "/":
            return walker_children[0] / walker_children[1]
        
        if myast.action == ">":
            return walker_children[0] > walker_children[1]
        
        if myast.action == "<":
            return walker_children[0] < walker_children[1]

        if myast.action == "neg":
            return -walker_children[0]
        
        if myast.action == "and":
            return walker_children[0] & walker_children[1]
        
        if myast.action == "or":
            return walker_children[0] | walker_children[1]

        if myast.action == "not":
            return ~walker_children[0]
        
        if myast.action == "astype":
            return walker_children[0].astype(walker_children[1])
        
        if myast.action == "index_of_max":
            series = walker_children[0]
            if not isinstance(series, pd.Series):
                raise Exception(f"unable to find index of maximum for object that is not Series {series}")
            if series.empty:
                return pd.NA
            return series.idxmax()
        
        if myast.action == "isna":
            return walker_children[0].isna()
        
        if myast.action == "slice_label":
            ser = walker_children[0]
            return ser.loc[walker_children[1]]
        
        if myast.action == "slice_index":
            ser = walker_children[0]
            return ser.iloc[walker_children[1]]

        if myast.action == "at_index":
            try:
                return walker_children[0].loc[walker_children[1]]
            except KeyError:
                return pd.NA
        
        if myast.action == "hstack":
            return pd.concat([walker(each_ast) for each_ast in myast.children], axis="columns")

        if myast.action == "groupby":
            return walker_children[0].groupby(walker_children[1])
        
        if myast.action == "alias":
            return walker_children[0]
        
        if myast.action == "declare":
            context[walker_children[0]] = walker_children[1]
            return None
        
        if myast.action == "refer":
            return context[walker_children[0]]

        if myast.action == "execute":
            *preliminary, last = myast.children
            for item in preliminary:
                walker(item)
            return walker(last)
            

        raise Exception(f"Unexpected Node: {myast.action}")

    return walker(myast)


def deeply_equal(left:ASTChild, right:ASTChild) -> bool:
    if isinstance(left, AST) and isinstance(right, AST):
        if left.action == right.action and len(left.children)==len(right.children):
            return all(map(deeply_equal, left.children, right.children))
    elif not isinstance(left, AST) and not isinstance(right, AST):
        return left == right
    #else:
        # one of the two IS an AST
    return False

          
def columns_required(myast:ASTChild) -> tuple[set[str], set[str]]:
    if not isinstance(myast, AST):
        return (set(), set())
    elif myast.action == "left_column":
        column_name:str = myast.children[0]  # type: ignore
        return ({column_name}, set())
    elif myast.action=="right_column":
        column_name:str = myast.children[0]  # type: ignore
        return (set(), {column_name})
    else:
        result = [columns_required(sub_ast) for sub_ast in myast.children]
        return (
            set().union(*(a for a,b in result)),
            set().union(*(b for a,b in result))
        )



def output_column_name(myast:ASTChild):
    def walker(myast:ASTChild) -> str:
        if not isinstance(myast, AST):
            return str(myast)
        else:                
            if myast.action == "left_column" or myast.action == "right_column":
                return myast.children[0]
            elif len(myast.children) == 0:
                return f"{myast.action  }"
            elif len(myast.children) == 1:
                return f"{myast.action  }({walker(myast.children[0])})"
            elif len(myast.children) == 2:
                if len(myast.action)==1:
                    return f"({walker(myast.children[0])} {myast.action} {walker(myast.children[1])})"
                else:
                    return f"{myast.action}({walker(myast.children[0])},{walker(myast.children[1])})"
            else:

                raise Exception(
                    "Expected Unary or Binary operation when determining output column name."
                    f"found an AST with {len(myast.children)=}:\n"
                    + myast._to_string()
                )
    return walker(myast)


def output_column_name_simple(myast:ASTChild):
    def walker(myast:ASTChild, accumulator:list[str]) -> list[str]:
        if not isinstance(myast, AST):
            return accumulator
        else:                
            if myast.action == "left_column" or myast.action == "right_column":
                return [*accumulator, myast.children[0]]
            elif len(myast.children) == 0:
                return [*accumulator, myast.action]
            elif myast.action == "alias":
                return [*accumulator, myast.children[1]]
            elif myast.action == "filter":
                return [*accumulator, *itertools.chain(walker(myast.children[0], []))]
            else:
                return [*accumulator, *itertools.chain(*[walker(item, []) for item in myast.children])]

    return walker(myast,[])[0]


def equal_or_contains(left:ASTChild, right:ASTChild) -> bool:
    if deeply_equal(left, right):
        return True
    elif isinstance(left, AST):
        return any(equal_or_contains(child, right) for child in left.children)
    else:
        return False


def follow_path(ast:ASTChild, path:list[int]):
    if not isinstance(ast, AST) and len(path)>0:
        raise Exception()
    result:ASTChild = ast
    for item in path:
        if isinstance(result, AST):
            result = result.children[item]
        else:
            raise Exception("Could not follow_path; tried to get child {item} of {result}")
    return result


def as_tuple(myast:ASTChild) -> Union[tuple, ASTChild]:
    if not isinstance(myast, AST):
        try:
            hash(myast)
        except TypeError as e:
            raise TypeError(f"Only hashable types are permitted in the AST. found value of type {type(myast)} with value {myast}")
        return myast
    else:
        return (myast.action, *map(as_tuple, myast.children))


def unique_subtrees(myast:ASTChild) -> dict[Union[tuple, ASTChild], list[list[int]]]:
    
    nodes_to_visit:deque[Path_Value] = (
        deque() 
        if not isinstance(myast, AST) else 
        deque(
            ([index], item  )
            for index, item
            in enumerate(myast.children)
        )
    )

    subtrees_seen:dict[Union[tuple, ASTChild], list[list[int]]]  = {
        as_tuple(myast):[[]]
    }

    while nodes_to_visit:
        path, item = nodes_to_visit.popleft()

        if isinstance(item, AST):
            hashed = as_tuple(item)
            if hashed not in subtrees_seen:
                subtrees_seen[hashed] = [path]
            else:
                subtrees_seen[hashed].append(path)

            if item.action!="left_column":
                nodes_to_visit.extend(
                    ([*path, index], child) for index, child in enumerate(item.children)
                )
    return subtrees_seen


def max_depth(myast:ASTChild):
    if not isinstance(myast, AST):
        return 0
    


def optimize(myast:ASTChild):
    
    if not isinstance(myast, AST):
        return myast
    
    myast = clone(myast)

    # obtain a list of repeated subtrees
    unique_subtrees_ = unique_subtrees(myast)
    repeated_subtrees:list[tuple[ASTChild, list[list[int]]]] = [
        (follow_path(myast, paths[0]), paths)
        for paths in unique_subtrees_.values()
        if len(paths)>1
    ]
    
    # get a list of declare and refer objects
    declared = [
        (
            paths,
            declare(f"subtree_{name}", tree),
            refer(f"subtree_{name}"),
        )
        for name, (tree, paths) 
        in enumerate(repeated_subtrees)
    ]

    # explode entries by `paths` such that there is one entry per path
    declared_exploded = [
        (path, declare, refer)
        for paths, declare, refer in declared 
        for path in paths
    ]
    
    # sort (inplace) declared_exploded by length of path
    declared_exploded.sort(
        key=lambda item:len(item[0]),
        reverse=True
    )

    # replace tree parts with refers
    for path, _declare, refer in  declared_exploded:
        *path_tail, path_head = path
        subtree_parent_ast = follow_path(myast, path_tail)
        if not isinstance(subtree_parent_ast, AST):
            raise Exception("Tried to replace subtree with reference during optimization but failed because the subtree parent did not have children.")
        subtree_parent_ast.children[path_head] = refer
    
    # confirm dependency order by swapping declarations that depend on each other
    swap_count = 0
    start_again = True
    while start_again and swap_count<50:
        start_again = False
        for i in range(len(declared)):
            for j in range(i+1, len(declared)):
                _, declare_first,  refer_first  = declared[i]
                _, declare_second, refer_second = declared[j]
                
                if equal_or_contains(declare_first, refer_second):
                    print("swap")
                    declared[i],declared[j] = declared[j],declared[i] 
                    swap_count += 1
                    start_again = True
                    break
            if start_again:
                break

    if start_again and swap_count==50:
        raise Exception("Compilation failed... probably caused by a circular reference. I thought it wasn't possible, but you did it!")
    
    return execute([declare for _path, declare, _refer in declared]+[myast])
