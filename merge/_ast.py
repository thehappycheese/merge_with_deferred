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
    "and",
    "or",
    "not",
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
    "slice",
    "declare",
    "refer",
    "execute"
]
ASTChild = Union["AST", float, int, bool, str]

Path_Value = tuple[list[int], ASTChild]



class AST_Slice_Maker:
    host:AST
    def __init__(self, host:AST) -> None:
        self.host = host
    def __getitem__(self, slicer:slice) -> AST:
        return AST("slice",[self.host, slicer])

class AST:
    action:Action
    children:list[ASTChild]
    
    def __init__(self, action:Action, children:list[ASTChild]):
        self.action   = action
        self.children = children
        self.loc = AST_Slice_Maker(self)
    
    def __repr__(self):
        return f"<AST {self.action}" + (
            f" {self.children[0]}>"
            if len(self.children) == 1 and not isinstance(self.children[0], AST) 
            else ">"
        )

    def to_string(self, indent:str="", is_parents_last=False)->str:
        if len(indent) != 0:
            modified_indent = indent[:-3]+" ┠╴"
            if is_parents_last:
                modified_indent = indent[:-3]+" ┖╴"
        else:
            modified_indent = indent
        

        out = f"\n{modified_indent}[{self.action}]"
        if len(self.children)>0:
            *children_tail, children_head = self.children
            for islast, child in is_last(iter(self.children)):
                if isinstance(child, AST):
                    out+=child.to_string(indent+(" ┃ " if not islast else "   "), islast)
                elif isinstance(child, str):
                    out+=f'\n{indent+(" ┖╴" if islast else " ┠╴")}"{child}"'
                else:
                    out+=f'\n{indent+(" ┖╴" if islast else " ┠╴")}{child}'
        return out

    @staticmethod
    def clone(myast:ASTChild) -> ASTChild:
        if not isinstance(myast, AST):
            return myast
        return AST(myast.action, [*map(AST.clone, myast.children)])

    @staticmethod
    def left_column(name:str) -> AST:
        return AST("left_column", [name])
    
    @staticmethod
    def right_column(name:str) -> AST:
        return AST("right_column", [name])
    
    @staticmethod
    def length_of_overlap() -> AST:
        return AST("length_of_overlap", [])
    
    @staticmethod
    def fraction_of_right() -> AST:
        return AST("fraction_of_right", [])

    @staticmethod
    def fraction_of_left() -> AST:
        return AST("fraction_of_left", [])
    
    @staticmethod
    def length_of_left() -> AST:
        return AST("length_of_left", [])
    
    @staticmethod
    def length_of_right() -> AST:
        return AST("length_of_right", [])

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
        return AST("==",[self, other])
    
    def __and__(self, other:ASTChild) -> AST:
        return AST("and", [self, other])
    
    def __or__(self, other:ASTChild) -> AST:
        return AST("or", [self, other])
    
    def __invert__(self) -> AST:
        return AST("not", [self])
    
    def sum(self) -> AST:
        return AST("sum",[self])
    
    def index_of_max(self) -> AST:
        return AST("index_of_max",[self])

    def at_index(self, idx:int) -> AST:
        return AST("at_index",[self, idx])
    
    def astype(self, typ:str) -> AST:
        return AST("astype",[self, typ]) # can only be applied to grouped?
    
    @staticmethod
    def execute(statements:list[AST]) ->AST:
        return AST("execute", statements)

    @staticmethod
    def declare(name:str, value:ASTChild) -> AST:
        return AST("declare", [name, value])

    @staticmethod
    def refer(name:str) -> AST:
        return AST("refer", [name])

    @staticmethod
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
            

            if myast.action == "filter":
                series = walker(myast.children[0])
                mask   = walker(myast.children[1])
                print("series",series)
                print("mask",  mask)
                assert mask.dtype == bool, "Filter is not a boolean series"
                assert (series.index == mask.index).all(), "Filter is not aligned to series"
                return series.loc[mask]

            if myast.action == "sum":
                return walker(myast.children[0]).sum()

            if myast.action == "+":
                return walker(myast.children[0]) + walker(myast.children[1])
            
            if myast.action == "-":
                return walker(myast.children[0]) - walker(myast.children[1])

            if myast.action == "*":
                return walker(myast.children[0]) * walker(myast.children[1])
            
            if myast.action == "/":
                return walker(myast.children[0]) / walker(myast.children[1])
            
            if myast.action == ">":
                return walker(myast.children[0]) > walker(myast.children[1])
            
            if myast.action == "<":
                return walker(myast.children[0]) < walker(myast.children[1])

            if myast.action == "neg":
                return -walker(myast.children[0])
            
            if myast.action == "and":
                return walker(myast.children[0]) & walker(myast.children[1])
            
            if myast.action == "or":
                return walker(myast.children[0]) | walker(myast.children[1])

            if myast.action == "not":
                return ~walker(myast.children[0])
            
            if myast.action == "astype":
                return walker(myast.children[0]).astype(walker(myast.children[1]))
            
            if myast.action == "index_of_max":
                ser = walker(myast.children[0])
                return ser.index[ser.argmax()]
            
            if myast.action == "slice":
                ser = walker(myast.children[0])
                return ser.loc[myast.children[1]]

            if myast.action == "at_index":
                return walker(myast.children[0]).loc[walker(myast.children[1])]
            
            if myast.action == "declare":
                context[myast.children[0]] = walker(myast.children[1])
            
            if myast.action == "refer":
                return context[myast.children[0]]

            if myast.action == "execute":
                *preliminary, last = myast.children
                for item in preliminary:
                    walker(item)
                return walker(last)
                

            raise Exception(f"Unexpected Node: {myast.action}")

        return walker(myast)
    
    @staticmethod
    def compare_equal(left:ASTChild, right:ASTChild) -> bool:
        if isinstance(left, AST) and isinstance(right, AST):
            if left.action == right.action and len(left.children)==len(right.children):
                return all(map(AST.compare_equal, left.children, right.children))
        elif not isinstance(left, AST) and not isinstance(right, AST):
            return left == right
        #else:
            # one of the two IS an AST
        return False
    
    @staticmethod          
    def columns_required(myast) -> tuple[set[str], set[str]]:
        if not isinstance(myast, AST):
            return (set(), set())
        elif myast.action == "left_column":
            column_name:str = myast.children[0]  # type: ignore
            return ({column_name}, set())
        elif myast.action=="right_column":
            column_name:str = myast.children[0]  # type: ignore
            return (set(), {column_name})
        else:
            result = [AST.columns_required(sub_ast) for sub_ast in myast.children]
            return (
                set().union(*(a for a,b in result)),
                set().union(*(b for a,b in result))
            )

    
    @staticmethod
    def output_column_name(myast:ASTChild):
        def walker(myast:ASTChild) -> str:
            if not isinstance(myast, AST):
                return str(myast)
            else:                
                if myast.action == "left_column" or myast.action == "right_column":
                    return myast.children[0]
                elif len(myast.children) == 1:
                    return f"{myast.action  }({walker(myast.children[0])})"
                elif len(myast.children) == 2:
                    if len(myast.action)==1:
                        return f"({walker(myast.children[0])} {myast.action} {walker(myast.children[1])})"
                    else:
                        return f"{myast.action}({walker(myast.children[0])},{walker(myast.children[1])})"
                else:
                    raise Exception("Expected Unary or Binary operation when determining output column name")
        return walker(myast)

    @staticmethod
    def follow_path(ast:ASTChild, path:list[int]):
        if not isinstance(ast, AST) and len(path)>0:
            raise Exception()
        result = ast
        for item in path:
            result = result.children[item]
        return result

    @staticmethod
    def output_column_name2(myast:ASTChild):
        result = ""
        def walker(myast:ASTChild, accumulator:list[str]) -> list[str]:
            nonlocal result
            if not isinstance(myast, AST):
                return accumulator
            else:                
                if myast.action == "left_column" or myast.action == "right_column":
                    return [*accumulator, myast.children[0]]
                elif myast.action == "alias":
                    return [*accumulator, myast.children[1]]
                elif myast.action == "filter":
                    return [*accumulator, *itertools.chain(walker(myast.children[0], []))]
                else:
                    return [*accumulator, *itertools.chain(*[walker(item, []) for item in myast.children])]

        return walker(myast,[])[-1]
    
    @staticmethod
    def as_tuple(myast:ASTChild) -> Union[tuple, ASTChild]:
        # TODO: ensure result is hashable and serializable or there will be consequences
        if not isinstance(myast, AST):
            return myast
        else:
            return (myast.action, *map(AST.as_tuple, myast.children))

    @staticmethod
    def unique_subtrees(myast:ASTChild):
        
        nodes_to_visit:deque[Path_Value] = (
            deque() 
            if not isinstance(myast, AST) else 
            deque(
                ([index], item  )
                for index, item
                in enumerate(myast.children)
            )
        )
        
        # abuse the use fact that pythons tuple is hashable if it contains hashable types; it can be used as a dict key
        # TODO: this will cause errors if our AST ever is allowed to capture non-hashable literal types
        subtrees_seen:dict[Union[tuple, ASTChild], list[list[int]]]  = {
            AST.as_tuple(myast):[[]]
        }

        while nodes_to_visit:
            path, item = nodes_to_visit.popleft()

            if isinstance(item, AST):
                hashed = AST.as_tuple(item)
                if hashed not in subtrees_seen:
                    subtrees_seen[hashed] = [path]
                else:
                    subtrees_seen[hashed].append(path)

                if item.action!="left_column":
                    nodes_to_visit.extend(
                        ([*path, index], child) for index, child in enumerate(item.children)
                    )
        return subtrees_seen
    
    @staticmethod
    def max_depth(myast:ASTChild):
        if not isinstance(myast, AST):
            return 0
        

    @staticmethod
    def execution_plan(myast:ASTChild):
        
        myast = AST.clone(myast)

        unique_subtrees = AST.unique_subtrees(myast)
        repeated_subtrees = [
            (AST.follow_path(myast, item[0]), item) for item in unique_subtrees.values()
            if len(item)>1
        ]

        # replace all like subtrees with a reference to the same instance
        # for _, path, subtree in sorted((-len(path), path, tree) for tree, paths in repeated_subtrees for path in paths):
        #     *path_tail, path_head = path
        #     print("======\n\n")
        #     print(f"will replace child {path_head} at {path_tail} with \n{subtree.to_string()}")
        #     AST.follow_path(myast, path_tail).children[path_head] = subtree
        
        # get a list of declare and refer objects
        declared = [
            (
                AST.declare(f"subtree_{name}", tree),
                AST.refer(f"subtree_{name}"),
                path
            )
            for name, (tree, path) 
            in enumerate(repeated_subtrees)
        ]

        # replace tree parts with refers
        for _, path, reference in  sorted((-len(path), path, refer) for declare, refer, paths in declared for path in paths):
            *path_tail, path_head = path
            AST.follow_path(myast, path_tail).children[path_head] = reference
        
        return AST.execute([declare for declare,_,_ in reversed(declared)]+[myast])

        

# {
#     ('-',  ('+',   ('*', ('+', ('left_column', 'A'), 5), 2),   ('*', ('*', ('+', ('left_column', 'A'), 5), 2), 3)),  ('*', ('+', ('left_column', 'A'), 5), 2)): [],
#     ('+',  ('*', ('+', ('left_column', 'A'), 5), 2),  ('*', ('*', ('+', ('left_column', 'A'), 5), 2), 3)): [[0]],
#     ('*', ('+', ('left_column', 'A'), 5), 2):              [[1], [0, 0], [0, 1, 0]],
#     ('*', ('*', ('+', ('left_column', 'A'), 5), 2), 3):    [[0, 1]],
#     ('+', ('left_column', 'A'), 5):                        [[1, 0], [0, 0, 0], [0, 1, 0, 0]],
#     ('left_column', 'A'):                                  [[1, 0, 0], [0, 0, 0, 0], [0, 1, 0, 0, 0]]
# }