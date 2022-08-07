"""Merge Abstract Syntax Tree"""
from dataclasses import dataclass
import operator
from typing import Callable, Literal, Type

BUILTIN_METHOD_TYPE = type(abs)

@dataclass
class MAST_Operator:
    
    long_name:str
    short_name:str
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
ops = [
    MAST_Operator("equal identity"            ,"equal_identity"          ,"α is ω"        , operator.is_,          2, False, lambda item:f"{item}"),
    MAST_Operator("not equal identity"        ,"not_equal_identity"      ,"α is not ω"    , operator.is_not,       2, False, lambda item:f"{item}"),
    MAST_Operator("equal value"               ,"equal_value"             ,"α == ω"        , operator.eq,           2, True,  lambda item:f"{item}"),
    MAST_Operator("not equal value"           ,"not_equal_value"         ,"α != ω"        , operator.ne,           2, False, lambda item:f"{item}"),
    MAST_Operator("greater than or equal"     ,"greater_than_or_equal"   ,"α >= ω"        , operator.ge,           2, False, lambda item:f"{item}"),
    MAST_Operator("greater_than"              ,"greater_than"            ,"α > ω"         , operator.gt,           2, False, lambda item:f"{item}"),
    MAST_Operator("less than or equal"        ,"less_than_or_equal"      ,"α <= ω"        , operator.le,           2, False, lambda item:f"{item}"),
    MAST_Operator("less than"                 ,"less_than"               ,"α < ω"         , operator.lt,           2, False, lambda item:f"{item}"),
    MAST_Operator("negative"                  ,"negative"                ,"- α"           , operator.neg,          1, False, lambda item:f"{item}"),
    MAST_Operator("absolute value"            ,"abs"                     ,"abs(α)"        , operator.abs,          1, False, lambda item:f"{item}"),
    MAST_Operator("add"                       ,"add"                     ,"α + ω"         , operator.add,          2, True,  lambda item:f"{item}"),
    MAST_Operator("sub"                       ,"sub"                     ,"α - ω"         , operator.sub,          2, False, lambda item:f"{item}"),
    MAST_Operator("mul"                       ,"mul"                     ,"α * ω"         , operator.mul,          2, True,  lambda item:f"{item}"),
    MAST_Operator("truediv"                   ,"truediv"                 ,"α / ω"         , operator.truediv,      2, False, lambda item:f"{item}"),
    MAST_Operator("floored division"          ,"floordiv"                ,"α // ω"        , operator.floordiv,     2, False, lambda item:f"{item}"),
    MAST_Operator("modulus"                   ,"modulus"                 ,"α % ω"         , operator.mod,          2, False, lambda item:f"{item}"),
    MAST_Operator("matrix multiply"           ,"matrix_multiply"         ,"α @ ω"         , operator.matmul,       2, False, lambda item:f"{item}"),
    MAST_Operator("bitwise and"               ,"bitwise_and"             ,"α & ω"         , operator.and_,         2, True, lambda item:f"{item}"),
    MAST_Operator("bitwise or"                ,"bitwise_or"              ,"α | ω"         , operator.or_,          2, True, lambda item:f"{item}"),
    MAST_Operator("bitwise exclusive or"      ,"bitwise_exclusive_or"    ,"α ^ ω"         , operator.xor,          2, True, lambda item:f"{item}"),
    MAST_Operator("logical inverse"           ,"logical_not"             ,"not α"         , operator.not_,         1, False, lambda item:f"{item}"),
    MAST_Operator("bitwise inverse"           ,"bitwise_inverse"         ,"~ α"           , operator.inv,          1, False, lambda item:f"{item}"),
    MAST_Operator("bitwise shift left"        ,"bitwise_shift_left"      ,"α << ω"        , operator.lshift,       2, False, lambda item:f"{item}"),
    MAST_Operator("bitwise shift right"       ,"bitwise_shift_right"     ,"α >> ω"        , operator.rshift,       2, False, lambda item:f"{item}"),
    MAST_Operator("concat"                    ,"concat"                  ,"α + ω"         , operator.concat,       2, False, lambda item:f"{item}"),
    MAST_Operator("contains"                  ,"contains"                ,"ω in α"        , operator.contains,     2, False, lambda item:f"{item}"),
    MAST_Operator("delitem"                   ,"delitem"                 ,"del α[ω]"      , operator.delitem,      2, False, lambda item:f"{item}"),
    MAST_Operator("get item at index"         ,"getitem"                 ,"α[ω]"          , operator.getitem,      2, False, lambda item:f"{item}"),
    MAST_Operator("index"                     ,"index"                   ,"α.__index__()" , operator.index,        1, False, lambda item:f"{item}"),
    MAST_Operator("pow"                       ,"pow"                     ,"α ** ω"        , operator.pow,          2, False, lambda item:f"{item}"),
    MAST_Operator("setitem"                   ,"setitem"                 ,"α[ω] = 2"      , operator.setitem,      2, False, lambda item:f"{item}"),
]