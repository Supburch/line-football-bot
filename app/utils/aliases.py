from typing import Dict, Any, TypedDict, Union

class FlexBubble(TypedDict, total=False):
    type: str
    size: str
    body: Dict[str, Any]
    header: Dict[str, Any]
    footer: Dict[str, Any]

FlexDict = Union[FlexBubble, Dict[str, object]]
MatchData = Dict[str, Any]
