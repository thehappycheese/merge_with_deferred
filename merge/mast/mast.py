"""Merge Abstract Syntax Tree"""
from __future__ import annotations
from ast import alias
from dataclasses import dataclass
import operator
from re import S
from typing import Callable, Literal, Union, Any
from .._util.nicks_itertools import is_last
BUILTIN_METHOD_TYPE = type(abs)

@dataclass
class OP_Info:
    name:str
    symbol:str
    builtin_function:Callable
    number_args:Literal[1,2]
    commutative:bool
    string_reconstruction:Callable

# MAST_Operator("attrgetter"                ,"attrgetter"  ,""  , operator.attrgetter,   1, False, lambda item:f"{item}"),
# MAST_Operator("itemgetter"                ,"itemgetter"  ,"", operator.itemgetter,   0, False, lambda item:f"{item}"),
# MAST_Operator("methodcaller"              ,"methodcaller"            ,""        , operator.methodcaller, 0, False, lambda item:f"{item}"),
# MAST_Operator("indexOf"                   ,"indexOf"                 ,""        , operator.indexOf,      0, False, lambda item:f"{item}"),
# MAST_Operator("pos"                       ,"pos"                     ,""        , operator.pos,          0, False, lambda item:f"{item}"),
# MAST_Operator("truth"                     ,"truth"                   ,""        , operator.truth,        1, False, lambda item:f"{item}"),
# MAST_Operator("delitem"                   ,"delitem"                 ,"del α[ω]"      , operator.delitem,      2, False, lambda α,ω: f"(del α[ω])"     ),
# MAST_Operator("setitem"                   ,"setitem"                 ,"α[ω] = 2"      , operator.setitem,      2, False, lambda α,ω,z: f"{α}[{ω}] = {z}"     ),
# MAST_Operator("concat"                    ,"concat"                  ,"α + ω"         , operator.concat,       2, False, lambda α,ω: f"({α} +  {ω})"     ),
# MAST_Operator("index"                     ,"index"                   ,"α.__index__()" , operator.index,        1, False, lambda α,ω: f"{α}.__index__()"  ),
class OP:
    not_equal_identity    = OP_Info("not equal identity"    , "α is not ω" , operator.is_not       , 2, False, lambda α,ω: f"({α} is not {ω})" )
    equal_identity        = OP_Info("equal identity"        , "α is ω"     , operator.is_          , 2, False, lambda α,ω: f"({α} is {ω})"     )
    contains              = OP_Info("contains"              , "ω in α"     , operator.contains     , 2, False, lambda α,ω: f"({ω} in {α})"     )
    equal_value           = OP_Info("equal value"           , "α == ω"     , operator.eq           , 2, True , lambda α,ω: f"({α} == {ω})"     )
    not_equal_value       = OP_Info("not equal value"       , "α != ω"     , operator.ne           , 2, False, lambda α,ω: f"({α} != {ω})"     )
    greater_than_or_equal = OP_Info("greater than or equal" , "α >= ω"     , operator.ge           , 2, False, lambda α,ω: f"({α} >= {ω})"     )
    greater_than          = OP_Info("greater_than"          , "α > ω"      , operator.gt           , 2, False, lambda α,ω: f"({α} >  {ω})"     )
    less_than_or_equal    = OP_Info("less than or equal"    , "α <= ω"     , operator.le           , 2, False, lambda α,ω: f"({α} <= {ω})"     )
    less_than             = OP_Info("less than"             , "α < ω"      , operator.lt           , 2, False, lambda α,ω: f"({α} <  {ω})"     )
    add                   = OP_Info("add"                   , "α + ω"      , operator.add          , 2, True , lambda α,ω: f"({α} +  {ω})"     )
    subtract              = OP_Info("subtract"              , "α - ω"      , operator.sub          , 2, False, lambda α,ω: f"({α} -  {ω})"     )
    multiply              = OP_Info("multiply"              , "α * ω"      , operator.mul          , 2, True , lambda α,ω: f"({α} *  {ω})"     )
    pow                   = OP_Info("pow"                   , "α ** ω"     , operator.pow          , 2, False, lambda α,ω: f"({α} ** {ω})"     )
    truediv               = OP_Info("truediv"               , "α / ω"      , operator.truediv      , 2, False, lambda α,ω: f"({α} /  {ω})"     )
    floordiv              = OP_Info("floored division"      , "α // ω"     , operator.floordiv     , 2, False, lambda α,ω: f"({α} // {ω})"     )
    modulus               = OP_Info("modulus"               , "α % ω"      , operator.mod          , 2, False, lambda α,ω: f"({α} %  {ω})"     )
    matrix_multiply       = OP_Info("matrix multiply"       , "α @ ω"      , operator.matmul       , 2, False, lambda α,ω: f"({α} @  {ω})"     )
    bitwise_shift_left    = OP_Info("bitwise shift left"    , "α << ω"     , operator.lshift       , 2, False, lambda α,ω: f"({α} << {ω})"     )
    bitwise_shift_right   = OP_Info("bitwise shift right"   , "α >> ω"     , operator.rshift       , 2, False, lambda α,ω: f"({α} >> {ω})"     )
    bitwise_and           = OP_Info("bitwise and"           , "α & ω"      , operator.and_         , 2, True , lambda α,ω: f"({α} &  {ω})"     )
    bitwise_or            = OP_Info("bitwise or"            , "α | ω"      , operator.or_          , 2, True , lambda α,ω: f"({α} |  {ω})"     )
    bitwise_exclusive_or  = OP_Info("bitwise exclusive or"  , "α ^ ω"      , operator.xor          , 2, True , lambda α,ω: f"({α} ^  {ω})"     )
    bitwise_inverse       = OP_Info("bitwise inverse"       , "~ α"        , operator.inv          , 1, False, lambda α  : f"(~{α})"           )
    get_item_at_index     = OP_Info("get item at index"     , "α[ω]"       , operator.getitem      , 2, False, lambda α,ω: f"{α}[{ω}]"         )
    negative              = OP_Info("negative"              , "- α"        , operator.neg          , 1, False, lambda α  : f"(-{α})"           )
    absolute              = OP_Info("absolute"              , "abs(α)"     , operator.abs          , 1, False, lambda α  : f"abs({α})"         )
    logical_not           = OP_Info("logical inverse"       , "not α"      , operator.not_         , 1, False, lambda α  : f"(not {α})"        )
    logical_and           = OP_Info("logical and"           , "α and ω"    , lambda α,ω  : α and ω   , 2, True , lambda α,ω  : f"({α} and {ω})"  )
    logical_or            = OP_Info("logical or"            , "α or ω"     , lambda α,ω  : α or  ω   , 2, True , lambda α,ω  : f"({α} or {ω})"   )
    get_attribute         = OP_Info("get attribute"         , "α"          , lambda α,ω  : α[ω]      , 2, False, lambda α,ω  : f"{α}.{ω}"        )
    call                  = OP_Info("call"                  , "α(...)"     , lambda α,ω,δ: α(*ω,**δ) , 1, False, lambda α,ω,δ: f"{α}(*{ω},**{δ})")
    slice_label           = OP_Info("slice label"           , "α.loc[ω]"   , lambda α,ω  : α.loc [ω] , 2, False, lambda α,ω  : f"({α}.loc[{ω}])" )
    slice_integer         = OP_Info("slice integer"         , "α.iloc[ω]"  , lambda α,ω  : α.iloc[ω] , 2, False, lambda α,ω  : f"({α}.iloc[{ω}])")
    alias                 = OP_Info("alias"                 , "α"          , lambda α    : α         , 1, False, lambda α    : f"{α}"            )
    column                = OP_Info("column"                , "α"          , lambda α    : α         , 1, False, lambda α    : f"{α}"            )

ASTChild = Union["AST", float, int, bool, str, slice]


class AST_Call:
    _ast_instance:AST
    def __init__(self, ast:AST) -> None:
        self._ast_instance = ast
    
    # def __getattribute__(self, __name: str) -> Any:
    #     pass

    def __getattribute__(self, __name: str) -> AST:
        if __name.startswith("__"):
            return object.__getattribute__(self, __name)
        else:
            return AST_Callable(OP.get_attribute, [object.__getattribute__(self,"_ast_instance"), __name])
        

class AST:
    
    action:OP_Info
    children:list[ASTChild]

    def __init__(self, op:OP_Info, args:list[ASTChild], /):
        self.action   = op
        self.children = args
        self.call     = AST_Call(self)
    
    def __repr__(self):
        return f"⟨AST {self.action.name}" + (
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
        

        out = f"\n{modified_indent}⟨{self.action.name}⟩"
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
    
    def __add__(self, other:ASTChild) -> AST:
        return AST(OP.add,          [self, other])

    def __sub__(self, other:ASTChild) -> AST:
        return AST(OP.subtract,     [self, other])

    def __mul__(self, other:ASTChild) -> AST:
        return AST(OP.multiply,     [self, other])

    def __truediv__(self, other:ASTChild) -> AST:
        return AST(OP.truediv,      [self, other])
    
    def __divmod__(self, other:ASTChild) ->AST:
        return AST(OP.floordiv,     [self, other])

    def __gt__(self, other:ASTChild) -> AST:
        return AST(OP.greater_than, [self, other])

    def __lt__(self, other:ASTChild) -> AST:
        return AST(OP.less_than,    [self, other])

    def __eq__(self, other:ASTChild) -> AST:
        return AST(OP.equal_value,  [self, other])

    def __and__(self, other:ASTChild) -> AST:
        return AST(OP.bitwise_and,  [self, other])

    def __or__(self, other:ASTChild) -> AST:
        return AST(OP.bitwise_or,   [self, other])

    def __invert__(self) -> AST:
        return AST(OP.logical_not,  [self])

    def __bool__(self):
        raise Exception(
            "Cannot use `and`, `not` and `or` because `PEP 335 - Overridable Boolean Operators` was rejected.\n"
            "Yay for python.\n"
            "It was because the `and` and `or` operators have special short-circuit behavior;\n"
            "the second operand of `or` will never be evaluated if the first operand evaluates to true.\n"
            "This builtin behavior conflicts with our Abstract Syntax Tree building endeavour.\n"
            "Please use `AST.logical_and(a,b)`, `AST.logical_or(a,b)` or `AST.logical_not(a)`.\n"
            "Still, I think it was a bad decision."
        )

    def slice_label(self, slicer:ASTChild) -> AST:
        return AST(OP.slice_label,   [self, slicer])

    def slice_integer(self, slicer:ASTChild) -> AST:
        return AST(OP.slice_integer, [self, slicer])

class AST_Callable(AST):
    def __call__(self, *args: Any, **kwds: Any) -> AST:
        return AST(OP.call, [self, args, kwds])




def column(name:str):
    return AST(OP.column, [name])

def call(function, *args, ** kwargs):
    return AST(OP.call, [function, *args, **kwargs])